"""scripts/build_hero_image.py: a real photo in, the hero's six WebP files out."""

import importlib.util
import io
from pathlib import Path

import pytest
from PIL import ExifTags, Image, ImageDraw

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "build_hero_image.py"
spec = importlib.util.spec_from_file_location("build_hero_image", SCRIPT)
assert spec is not None and spec.loader is not None
hero = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hero)

EXPECTED = {
    "hero-portrait-600.webp": (600, 750),
    "hero-portrait-900.webp": (900, 1125),
    "hero-portrait-1200.webp": (1200, 1500),
    "hero-wide-960.webp": (960, 540),
    "hero-wide-1440.webp": (1440, 810),
    "hero-wide-1920.webp": (1920, 1080),
}


def portrait_photo(path: Path, size: tuple[int, int] = (2000, 3000)) -> Path:
    """A tall photo, red in its top tenth and blue below, with GPS and a camera make.

    Red only at the very top, so a crop pushed to the bottom starts in the blue:
    even the tall 4:5 crop of a 2:3 photo begins a sixth of the way down then.
    """
    image = Image.new("RGB", size, (30, 60, 220))
    ImageDraw.Draw(image).rectangle((0, 0, size[0], size[1] // 10), fill=(220, 30, 30))
    exif = Image.Exif()
    exif[ExifTags.Base.Make] = "TattleCam"
    exif.get_ifd(ExifTags.IFD.GPSInfo)[ExifTags.GPS.GPSLatitudeRef] = "N"
    image.save(path, "JPEG", quality=92, exif=exif)
    return path


def top_colour(path: Path) -> str:
    image = Image.open(path).convert("RGB")
    pixel = image.getpixel((image.width // 2, 5))
    assert isinstance(pixel, tuple)
    return "red" if pixel[0] > pixel[2] else "blue"


def test_one_photo_makes_both_crops_at_every_width(tmp_path: Path) -> None:
    written = hero.build(portrait_photo(tmp_path / "in.jpg"), tmp_path / "out")

    assert sorted(path.name for path in written) == sorted(EXPECTED)
    for path in written:
        assert Image.open(path).format == "WEBP"
        assert Image.open(path).size == EXPECTED[path.name]


def test_every_file_fits_the_hero_budget_and_carries_no_metadata(tmp_path: Path) -> None:
    for path in hero.build(portrait_photo(tmp_path / "in.jpg"), tmp_path / "out"):
        data = path.read_bytes()
        image = Image.open(io.BytesIO(data))
        assert len(data) <= hero.HERO_BUDGET_BYTES
        assert not image.getexif()
        assert b"TattleCam" not in data


def test_focus_moves_the_crop(tmp_path: Path) -> None:
    photo = portrait_photo(tmp_path / "in.jpg")

    high = hero.build(photo, tmp_path / "high", portrait_focus=0.0, wide_focus=0.0)
    low = hero.build(photo, tmp_path / "low", portrait_focus=1.0, wide_focus=1.0)

    assert all(top_colour(path) == "red" for path in high)
    assert all(top_colour(path) == "blue" for path in low)


def test_a_separate_wide_photo_is_used_for_laptops(tmp_path: Path) -> None:
    landscape = tmp_path / "wide.jpg"
    Image.new("RGB", (3000, 2000), (30, 180, 60)).save(landscape, "JPEG")

    photo = portrait_photo(tmp_path / "in.jpg")
    written = hero.build(photo, tmp_path / "out", wide_photo=landscape)

    wide = Image.open(tmp_path / "out" / "hero-wide-1920.webp").convert("RGB")
    assert wide.getpixel((960, 540)) == pytest.approx((30, 180, 60), abs=12)
    assert len(written) == len(EXPECTED)


def test_a_photo_too_small_for_the_wide_crop_is_refused(tmp_path: Path) -> None:
    """A 1500 px wide photo can't make a 1920 px hero without enlarging it."""
    small = portrait_photo(tmp_path / "small.jpg", size=(1500, 2200))

    assert hero.main([str(small), "--out", str(tmp_path / "out")]) == 1


def test_focus_must_be_a_fraction() -> None:
    with pytest.raises(SystemExit):
        hero.main(["photo.jpg", "--portrait-focus", "2"])
