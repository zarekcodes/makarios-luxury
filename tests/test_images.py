"""The image pipeline (#28): one photo in, three small WebP files out.

Every photo here is drawn by the test, in memory, so each one is built to show
one thing: a red stripe that a centre crop must cut, a top half that an EXIF
rotation must move to the side, a GPS tag that must not survive.
"""

import io
import random
import struct
import zlib

import pytest
from PIL import ExifTags, Image, ImageCms, ImageDraw, ImageFilter

from app.paths import STATIC_DIR
from app.services.images import (
    MAX_LARGEST_BYTES,
    WIDTHS,
    PhotoRejected,
    file_name,
    height_for,
    process_photo,
)

RED, GREEN, BLUE = (220, 30, 30), (30, 180, 60), (30, 60, 220)


def textured(size: tuple[int, int], seed: int = 0) -> Image.Image:
    """Soft noise over a gradient: compresses about like a real photo, unlike flat colour."""
    width, height = size
    noise = Image.frombytes("RGB", size, random.Random(seed).randbytes(width * height * 3))
    gradient = Image.linear_gradient("L").resize(size).convert("RGB")
    return Image.blend(gradient, noise.filter(ImageFilter.GaussianBlur(2)), 0.25)


def encode(image: Image.Image, format: str = "JPEG", **options: object) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format, **options)
    return buffer.getvalue()


def open_webp(data: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(data))
    assert image.format == "WEBP"
    return image


def colour_at(image: Image.Image, x: float, y: float) -> tuple[int, int, int]:
    """The pixel at a fraction of the way across and down."""
    pixel = image.convert("RGB").getpixel((int(x * (image.width - 1)), int(y * (image.height - 1))))
    assert isinstance(pixel, tuple)
    return pixel[0], pixel[1], pixel[2]


def closest(colour: tuple[int, int, int]) -> str:
    named = {"red": RED, "green": GREEN, "blue": BLUE, "white": (255, 255, 255)}
    return min(
        named, key=lambda name: sum((a - b) ** 2 for a, b in zip(named[name], colour, strict=True))
    )


@pytest.mark.parametrize("size", [(4000, 3000), (3024, 4032)], ids=["landscape", "portrait"])
def test_a_photo_becomes_three_4_by_5_webp_files(size: tuple[int, int]) -> None:
    photo = process_photo(encode(textured(size), quality=92))

    assert sorted(photo.files) == list(WIDTHS)
    for width, data in photo.files.items():
        assert open_webp(data).size == (width, height_for(width))
    assert height_for(1200) == 1500


def test_a_landscape_photo_keeps_its_centre() -> None:
    """A 4:3 photo is wider than 4:5, so the crop takes the middle and drops both sides."""
    image = Image.new("RGB", (4000, 3000), GREEN)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 700, 3000), fill=RED)
    draw.rectangle((3300, 0, 4000, 3000), fill=BLUE)

    photo = process_photo(encode(image, quality=95))

    largest = open_webp(photo.files[1200])
    assert closest(colour_at(largest, 0.01, 0.5)) == "green"
    assert closest(colour_at(largest, 0.99, 0.5)) == "green"


def test_a_portrait_photo_keeps_its_middle_band() -> None:
    """A 3:4 photo is taller than 4:5, so the crop trims the top and bottom.

    3000 wide at 4:5 is 3750 tall, so 125 px go from each end of the 4000.
    """
    image = Image.new("RGB", (3000, 4000), GREEN)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 3000, 100), fill=RED)
    draw.rectangle((0, 3900, 3000, 4000), fill=BLUE)

    largest = open_webp(process_photo(encode(image, quality=95)).files[1200])

    assert closest(colour_at(largest, 0.5, 0.0)) == "green"
    assert closest(colour_at(largest, 0.5, 1.0)) == "green"


def phone_photo() -> bytes:
    """A JPEG as a phone saves it: stored sideways, with GPS, a camera make and XMP.

    The pixels are a landscape with red on top. The orientation tag (6) says
    "turn me 90 degrees clockwise to view", which moves the red to the right.
    """
    image = Image.new("RGB", (4000, 3000), BLUE)
    ImageDraw.Draw(image).rectangle((0, 0, 4000, 1500), fill=RED)
    exif = Image.Exif()
    exif[ExifTags.Base.Orientation] = 6
    exif[ExifTags.Base.Make] = "TattleCam"
    gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
    gps[ExifTags.GPS.GPSLatitudeRef] = "N"
    gps[ExifTags.GPS.GPSLatitude] = (33.0, 6.0, 7.0)
    xmp = b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:Description photographer="Ann"/></x:xmpmeta>'
    return encode(image, quality=95, exif=exif, xmp=xmp)


def test_the_phone_s_rotation_is_applied() -> None:
    largest = open_webp(process_photo(phone_photo()).files[1200])

    assert closest(colour_at(largest, 0.9, 0.5)) == "red"
    assert closest(colour_at(largest, 0.1, 0.5)) == "blue"


def test_metadata_is_stripped() -> None:
    """No GPS, no camera details, no XMP: nothing that says where or by whom."""
    source = phone_photo()
    assert b"TattleCam" in source

    for data in process_photo(source).files.values():
        image = open_webp(data)
        assert not image.getexif()
        assert {"exif", "xmp", "icc_profile"}.isdisjoint(image.info)
        assert b"TattleCam" not in data
        assert b"photographer" not in data


def test_a_colour_profile_is_converted_then_dropped() -> None:
    """The output is untagged sRGB, which every browser assumes for an untagged image."""
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    image = Image.new("RGB", (1600, 2000), GREEN)

    photo = process_photo(encode(image, quality=95, icc_profile=srgb))

    largest = open_webp(photo.files[1200])
    assert "icc_profile" not in largest.info
    assert closest(colour_at(largest, 0.5, 0.5)) == "green"


def test_transparency_is_flattened_onto_white() -> None:
    image = Image.new("RGBA", (1600, 2000), (0, 0, 0, 0))
    ImageDraw.Draw(image).ellipse((400, 500, 1200, 1500), fill=(*GREEN, 255))

    largest = open_webp(process_photo(encode(image, "PNG")).files[1200])

    assert largest.mode == "RGB"
    assert closest(colour_at(largest, 0.02, 0.02)) == "white"
    assert closest(colour_at(largest, 0.5, 0.5)) == "green"


def test_the_largest_file_fits_the_budget_at_full_quality() -> None:
    photo = process_photo(encode(textured((4000, 3000)), quality=92))

    assert len(photo.files[1200]) <= MAX_LARGEST_BYTES
    assert photo.quality == 80
    assert len(photo.files[400]) < len(photo.files[800]) < len(photo.files[1200])


def test_a_photo_too_detailed_for_the_budget_is_refused() -> None:
    """Pure noise is the worst case: no quality setting gets it under the budget."""
    noise = Image.frombytes("RGB", (1200, 1500), random.Random(1).randbytes(1200 * 1500 * 3))

    with pytest.raises(PhotoRejected, match="too much fine detail"):
        process_photo(encode(noise, "PNG"))


@pytest.mark.parametrize(
    "data",
    [b"%PDF-1.7\n1 0 obj << /Type /Catalog >> endobj", b"just some text", b""],
    ids=["pdf", "text", "empty"],
)
def test_a_file_that_is_not_an_image_is_refused(data: bytes) -> None:
    with pytest.raises(PhotoRejected, match="isn't a photo"):
        process_photo(data)


def test_an_unsupported_image_format_is_refused() -> None:
    with pytest.raises(PhotoRejected, match="GIF files aren't supported"):
        process_photo(encode(Image.new("RGB", (1600, 2000), GREEN), "GIF"))


def test_a_file_over_the_limit_is_refused_before_it_is_opened() -> None:
    """The size check comes first: an oversized file isn't even decoded."""
    with pytest.raises(PhotoRejected, match=r"That file is 2 MB\. Photos can be up to 1 MB\."):
        process_photo(b"\0" * (1024 * 1024 + 1), max_bytes=1024 * 1024)


def test_a_photo_too_small_for_the_largest_width_is_refused() -> None:
    """Enlarging a small photo to 1200 px would only make it blurry."""
    with pytest.raises(PhotoRejected, match=r"too small \(1000×1000\).*1200×1500"):
        process_photo(encode(textured((1000, 1000))))


def png_header_only(width: int, height: int) -> bytes:
    """A PNG that claims a size and holds no pixels: how a decompression bomb starts."""

    def chunk(kind: bytes, body: bytes) -> bytes:
        checksum = struct.pack(">I", zlib.crc32(kind + body))
        return struct.pack(">I", len(body)) + kind + body + checksum

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IEND", b"")


@pytest.mark.parametrize("side", [9000, 30000], ids=["over-our-limit", "over-pillow-s-limit"])
def test_a_decompression_bomb_is_refused_before_it_is_unpacked(side: int) -> None:
    with pytest.raises(PhotoRejected, match="more than 80 megapixels"):
        process_photo(png_header_only(side, side))


def test_a_truncated_photo_is_refused() -> None:
    data = encode(textured((1600, 2000)), quality=92)

    with pytest.raises(PhotoRejected, match="damaged or incomplete"):
        process_photo(data[: len(data) // 2])


def test_file_names_match_what_responsive_img_serves() -> None:
    """The templates ask for <name>-<width>.webp; the placeholders already follow it."""
    assert file_name("watch-01", 400) == "watch-01-400.webp"
    for width in WIDTHS:
        assert (STATIC_DIR / "img" / "placeholder" / file_name("watch-01", width)).exists()
