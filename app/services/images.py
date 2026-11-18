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
    image = _crop_to_shape(load_photo(data, max_bytes))
    quality, files = encode_widths(image, WIDTHS, (ASPECT_WIDTH, ASPECT_HEIGHT), MAX_LARGEST_BYTES)
    return ProcessedPhoto(files=files, quality=quality)


def load_photo(data: bytes, max_bytes: int = MAX_UPLOAD_BYTES) -> Image.Image:
    """Steps 1 to 3: the photo checked, turned upright, and in sRGB, ready to crop.

    Raises PhotoRejected for a file that's too big, isn't a photo, or claims
    too many pixels.
    """
    return _to_srgb(ImageOps.exif_transpose(_open(data, max_bytes)))


def crop_to_aspect(
    image: Image.Image, aspect: tuple[int, int], focus: tuple[float, float] = (0.5, 0.5)
) -> Image.Image:
    """The largest rectangle of the given shape, centred as near `focus` as fits.

    focus is a fraction across and down: (0.5, 0.5) is the middle, (0.5, 0.3)
    keeps more of the top. The crop never runs off the photo, so a focus too
    near an edge just stops at that edge.
    """
    aspect_width, aspect_height = aspect
    width = min(image.width, image.height * aspect_width // aspect_height)
    height = width * aspect_height // aspect_width
    left = round(focus[0] * image.width - width / 2)
    top = round(focus[1] * image.height - height / 2)
    left = max(0, min(left, image.width - width))
    top = max(0, min(top, image.height - height))
    return image.crop((left, top, left + width, top + height))


def encode_widths(
    image: Image.Image, widths: tuple[int, ...], aspect: tuple[int, int], budget: int
) -> tuple[int, dict[int, bytes]]:
    """Step 5: WebP bytes at each width, all at one quality, the largest within `budget`.

    The quality is the best in QUALITY_STEPS whose largest file fits; the
    smaller files are made at the same quality, so they all look alike.
    Raises PhotoRejected if even the lowest step is over the budget.
    """
    aspect_width, aspect_height = aspect

    def resized(width: int) -> Image.Image:
        height = width * aspect_height // aspect_width
        # reducing_gap shrinks by whole steps first, then filters the last bit:
        # several times faster on a 12-megapixel photo, with no visible difference.
        return image.resize((width, height), Image.Resampling.LANCZOS, reducing_gap=3.0)

    largest = resized(widths[-1])
    for quality in QUALITY_STEPS:
        encoded = _encode(largest, quality)
        if len(encoded) <= budget:
            files = {width: _encode(resized(width), quality) for width in widths[:-1]}
            files[widths[-1]] = encoded
            return quality, files
    raise PhotoRejected(
        "That photo has too much fine detail to load quickly on a phone. "
        "Try a shot with a plainer background."
    )


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
    return crop_to_aspect(image, (ASPECT_WIDTH, ASPECT_HEIGHT))


def _encode(image: Image.Image, quality: int) -> bytes:
    """WebP bytes with no metadata: Pillow writes EXIF, XMP or a profile only if handed one."""
    buffer = io.BytesIO()
    image.info.clear()
    image.save(buffer, "WEBP", quality=quality, method=WEBP_METHOD)
    return buffer.getvalue()


def _too_many_pixels() -> PhotoRejected:
    megapixels = MAX_PIXELS // 1_000_000
    return PhotoRejected(f"That photo has more than {megapixels} megapixels. Resize it first.")


def _megabytes(size: int) -> str:
    return f"{math.ceil(size / (1024 * 1024))} MB"
