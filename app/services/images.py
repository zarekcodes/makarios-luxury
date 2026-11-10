"""The image pipeline: one photo from an owner in, small fast WebP files out.

process_photo() takes the bytes of an uploaded photo and returns the same
picture as WebP files 400, 800 and 1200 px wide, each cropped to the cards'
4:5 portrait shape, with every byte of metadata left behind. Where those files
are stored is photo upload's job (#68); this module only turns bytes into bytes.

Each step, in order, and why:

1. Refuse it before decoding if the file is too big, isn't an image, or claims
   more pixels than any phone takes. That last one stops a "decompression
   bomb": a tiny file whose header promises a 50,000 px square, which would
   need gigabytes of memory to unpack.
2. Turn it upright. Phones store a photo the way the sensor saw it and add an
   EXIF "orientation" tag that says how to rotate it. Stripping the metadata
   without applying the tag first would leave portrait shots on their side.
3. Convert its colours to sRGB. Recent iPhones and many Androids shoot in
   Display P3, a wider colour space, and tag the file with a profile saying so.
   The profile is metadata too, and dropped, and a browser shows an untagged
   image as sRGB. Unconverted, a P3 photo would look dull and slightly off.
4. Crop the centre to 4:5, then resize to each width.
5. Encode as WebP with no metadata at all: no EXIF (so no GPS, no camera
   serial), no XMP, no colour profile.
"""

import io
import math
from dataclasses import dataclass

from PIL import Image, ImageCms, ImageOps, UnidentifiedImageError

# The widths the templates' responsive_img() asks for, smallest first. The
# browser picks the one that fits the screen.
WIDTHS = (400, 800, 1200)

# The cards' shape: 4 wide by 5 tall.
ASPECT_WIDTH, ASPECT_HEIGHT = 4, 5

# A phone photo is 2-8 MB; a high-resolution one from a camera, up to about 20.
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

# 80 megapixels: more than a phone's normal photo (12-50), far below a bomb's
# claims, and under the 89 at which Pillow starts warning about bombs itself.
MAX_PIXELS = 80_000_000

# The largest file's ceiling. On a phone, the 800 px file is usually the one
# used; the 1200 px file serves high-density screens and laptops.
MAX_LARGEST_BYTES = 250_000

# WebP quality to try, best first. 80 is where a photo stops looking better to
# the eye; the lower steps only matter for an unusually detailed shot.
QUALITY_STEPS = (80, 70, 60, 50)

# 4 of WebP's 0-6 effort levels. 6 makes files under 1% smaller and takes
# twice as long, which an owner waiting on an upload would notice.
WEBP_METHOD = 4

# What Pillow calls the formats a phone or a laptop saves photos in. "MPO" is
# a JPEG with a second, smaller picture inside, which many phones write.
ACCEPTED_FORMATS = {"JPEG", "MPO", "PNG", "WEBP"}

_SRGB = ImageCms.createProfile("sRGB")


class PhotoRejected(ValueError):
    """A photo the pipeline won't take. The message is written for the owner."""


@dataclass(frozen=True)
class ProcessedPhoto:
    """One photo, ready to serve: WebP bytes for each width in WIDTHS."""

    files: dict[int, bytes]
    # The WebP quality all the files were made at.
    quality: int


def height_for(width: int) -> int:
    """A file's height at a given width, for the <img> tag's height attribute."""
    return width * ASPECT_HEIGHT // ASPECT_WIDTH


def file_name(name: str, width: int) -> str:
    """The name responsive_img() looks for: "watch-01" at 400 px is "watch-01-400.webp"."""
    return f"{name}-{width}.webp"


def process_photo(data: bytes, max_bytes: int = MAX_UPLOAD_BYTES) -> ProcessedPhoto:
    """Turn an uploaded photo into WebP files at every width in WIDTHS.

    Raises PhotoRejected, with a message for the owner, for a file that's too
    big, isn't a photo, is too small for the largest width, or is too detailed
    to fit the size budget.
    """
    image = _open(data, max_bytes)
    image = ImageOps.exif_transpose(image)
    image = _to_srgb(image)
    image = _crop_to_shape(image)

    quality, largest = _encode_within_budget(image, WIDTHS[-1])
    files = {width: _encode(_resize(image, width), quality) for width in WIDTHS[:-1]}
    files[WIDTHS[-1]] = largest
    return ProcessedPhoto(files=files, quality=quality)


def _open(data: bytes, max_bytes: int) -> Image.Image:
    if len(data) > max_bytes:
        raise PhotoRejected(
            f"That file is {_megabytes(len(data))}. Photos can be up to {_megabytes(max_bytes)}."
        )

    try:
        # open() reads only the header, so the checks below run before the
        # pixels are unpacked.
        image = Image.open(io.BytesIO(data))
    except (UnidentifiedImageError, OSError):
        raise PhotoRejected("That file isn't a photo. Upload a JPEG, PNG or WebP.") from None
    except Image.DecompressionBombError:
        raise _too_many_pixels() from None

    if image.format not in ACCEPTED_FORMATS:
        raise PhotoRejected(
            f"{image.format} files aren't supported. Upload a JPEG, PNG or WebP. "
            "On an iPhone, Settings > Camera > Formats > Most Compatible saves JPEGs."
        )
    if image.width * image.height > MAX_PIXELS:
        raise _too_many_pixels()

    try:
        image.load()
    except (OSError, Image.DecompressionBombError):
        raise PhotoRejected(
            "That photo is damaged or incomplete. Try exporting it again."
        ) from None
    return image


def _to_srgb(image: Image.Image) -> Image.Image:
    """The photo in plain 8-bit sRGB, with transparency flattened onto white.

    The colour conversion comes first, while the pixels are still in the mode
    the profile describes (a CMYK profile only makes sense on CMYK pixels).
    """
    profile = image.info.get("icc_profile")
    if profile and image.mode in ("RGB", "RGBA", "CMYK"):
        try:
            source = ImageCms.ImageCmsProfile(io.BytesIO(profile))
            output_mode = "RGBA" if image.mode == "RGBA" else "RGB"
            image = ImageCms.profileToProfile(image, source, _SRGB, outputMode=output_mode)
        except ImageCms.PyCMSError:
            pass  # A broken profile: keep the colours as they are, rather than refuse the photo.

    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        image = Image.new("RGB", rgba.size, "white")
        image.paste(rgba, mask=rgba.getchannel("A"))
    elif image.mode != "RGB":
        image = image.convert("RGB")
    return image


def _crop_to_shape(image: Image.Image) -> Image.Image:
    """The largest 4:5 rectangle from the centre of the photo.

    Refuses a photo too small to fill the largest width without enlarging it,
    which would only make it blurry.
    """
    crop_width = min(image.width, image.height * ASPECT_WIDTH // ASPECT_HEIGHT)
    if crop_width < WIDTHS[-1]:
        need_width, need_height = WIDTHS[-1], height_for(WIDTHS[-1])
        raise PhotoRejected(
            f"That photo is too small ({image.width}×{image.height}). "
            f"It needs at least {need_width}×{need_height} pixels."
        )
    crop_height = height_for(crop_width)
    left = (image.width - crop_width) // 2
    top = (image.height - crop_height) // 2
    return image.crop((left, top, left + crop_width, top + crop_height))


def _resize(image: Image.Image, width: int) -> Image.Image:
    # reducing_gap shrinks by whole steps first, then filters the last bit:
    # several times faster on a 12-megapixel photo, with no visible difference.
    return image.resize((width, height_for(width)), Image.Resampling.LANCZOS, reducing_gap=3.0)


def _encode(image: Image.Image, quality: int) -> bytes:
    """WebP bytes with no metadata: Pillow writes EXIF, XMP or a profile only if handed one."""
    buffer = io.BytesIO()
    image.info.clear()
    image.save(buffer, "WEBP", quality=quality, method=WEBP_METHOD)
    return buffer.getvalue()


def _encode_within_budget(image: Image.Image, width: int) -> tuple[int, bytes]:
    """The best quality whose largest file fits MAX_LARGEST_BYTES, and that file."""
    resized = _resize(image, width)
    for quality in QUALITY_STEPS:
        encoded = _encode(resized, quality)
        if len(encoded) <= MAX_LARGEST_BYTES:
            return quality, encoded
    raise PhotoRejected(
        "That photo has too much fine detail to load quickly on a phone. "
        "Try a shot with a plainer background."
    )


def _too_many_pixels() -> PhotoRejected:
    megapixels = MAX_PIXELS // 1_000_000
    return PhotoRejected(f"That photo has more than {megapixels} megapixels. Resize it first.")


def _megabytes(size: int) -> str:
    return f"{math.ceil(size / (1024 * 1024))} MB"
