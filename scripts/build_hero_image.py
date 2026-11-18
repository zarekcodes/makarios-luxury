"""Make the landing page's hero images from one or two real photos.

    uv run python scripts/build_hero_image.py design/photos/hero/GP/GP_roll.jpeg

The hero is art-directed: phones get a 4:5 portrait crop (600, 900, 1200 px)
and landscape screens a 16:9 wide crop (960, 1440, 1920 px). This writes both
to app/static/img/hero/, the names pages/home.html serves, as WebP with every
byte of metadata stripped, through the same pipeline as owners' uploads
(app/services/images.py). The repo is public, so never commit an original:
those stay in design/photos/, which is gitignored.

Trying candidates: run it on each, refresh the local site, and compare at phone
width and on a laptop. `git restore app/static/img/hero` puts back the hero
that's committed. Commit only the winner, and update the hero's alt text in
pages/home.html to describe it.

Framing:
  --portrait-focus  where the 4:5 crop sits, 0 at the top to 1 at the bottom.
                    The headline covers the lower part on phones, so the watch
                    should end up in the top half.
  --wide-focus      where the 16:9 strip sits, likewise. From a portrait photo
                    it spans the full width, so the watch stays central, under
                    the text. A landscape shot with the watch on the right
                    (--wide-photo) suits laptops better.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.services import images  # noqa: E402

DEFAULT_OUT = REPO_ROOT / "app" / "static" / "img" / "hero"

# The hero is the largest image on the page and the first to load, so the
# landing page's speed is mostly its weight. tests/test_landing.py holds every
# hero file to this budget.
HERO_BUDGET_BYTES = 150_000

CROPS = {
    "hero-portrait": {"aspect": (4, 5), "widths": (600, 900, 1200)},
    "hero-wide": {"aspect": (16, 9), "widths": (960, 1440, 1920)},
}


def build(
    photo: Path,
    out_dir: Path,
    *,
    wide_photo: Path | None = None,
    portrait_focus: float = 0.5,
    wide_focus: float = 0.5,
) -> list[Path]:
    """Write both crops of the hero into out_dir and return the files written."""
    sources = {"hero-portrait": photo, "hero-wide": wide_photo or photo}
    focus = {"hero-portrait": portrait_focus, "hero-wide": wide_focus}
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for name, crop in CROPS.items():
        image = images.load_photo(sources[name].read_bytes())
        image = images.crop_to_aspect(image, crop["aspect"], (0.5, focus[name]))
        widest = crop["widths"][-1]
        if image.width < widest:
            raise images.PhotoRejected(
                f"{sources[name].name} gives a {image.width} px wide {name} crop; "
                f"it needs at least {widest} px."
            )
        _, files = images.encode_widths(image, crop["widths"], crop["aspect"], HERO_BUDGET_BYTES)
        for width, data in files.items():
            path = out_dir / images.file_name(name, width)
            path.write_bytes(data)
            written.append(path)
    return written


def fraction(text: str) -> float:
    value = float(text)
    if not 0 <= value <= 1:
        raise argparse.ArgumentTypeError("use a number from 0 (top) to 1 (bottom)")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("photo", type=Path, help="the hero photo (used for both crops by default)")
    parser.add_argument("--wide-photo", type=Path, help="a separate landscape photo for laptops")
    parser.add_argument("--portrait-focus", type=fraction, default=0.5)
    parser.add_argument("--wide-focus", type=fraction, default=0.5)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    try:
        written = build(
            args.photo,
            args.out,
            wide_photo=args.wide_photo,
            portrait_focus=args.portrait_focus,
            wide_focus=args.wide_focus,
        )
    except images.PhotoRejected as rejected:
        print(f"error: {rejected}", file=sys.stderr)
        return 1

    for path in written:
        shown = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        print(f"wrote {shown} ({path.stat().st_size:,} bytes)")
    print("\nRefresh the local site to see it. `git restore app/static/img/hero` undoes this.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
