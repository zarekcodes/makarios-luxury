"""Derive the site's logo and favicon files from the design sources.

The originals in design/ are gitignored, so this script only runs on a machine
that has them. Its *outputs* are committed under app/static/img/brand/, which
is why a fresh clone can still build and serve the site.

Run it after changing a logo:

    uv run python scripts/build_brand_assets.py

Source of truth is the transparent circle badge. The horizontal wordmark PNG
has a solid black background, so it cannot sit on a light header; the site
composes its own lockup instead (see templates/partials/_brandmark.html).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO_ROOT / "design" / "logo" / "Makarios-Circle-Logo-Transparent.png"
DEFAULT_OUT = REPO_ROOT / "app" / "static" / "img" / "brand"

# The badge renders at 36 CSS px in the header, so 72 and 108 cover 2x and 3x
# screens. 180 is the Apple touch icon size; 32 is the classic favicon.
BADGE_WIDTHS = (72, 108)
FAVICON_SIZE = 32
TOUCH_ICON_SIZE = 180

# Favicons and touch icons are composited onto the brand blue, because a
# transparent PNG disappears against a dark browser tab strip.
BRAND_BLUE = (15, 82, 186, 255)


def load_badge(source: Path) -> Image.Image:
    """Load the badge and crop away fully transparent margins."""
    badge = Image.open(source).convert("RGBA")
    bbox = badge.getbbox()
    if bbox is not None:
        badge = badge.crop(bbox)
    return badge


def square(image: Image.Image) -> Image.Image:
    """Pad to a square so resizing never distorts the circle."""
    side = max(image.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    return canvas


def on_brand_blue(image: Image.Image, size: int) -> Image.Image:
    """Flatten onto the brand blue, for icons that need an opaque background."""
    scaled = image.resize((size, size), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), BRAND_BLUE)
    canvas.alpha_composite(scaled)
    return canvas


def build(source: Path, out_dir: Path) -> list[Path]:
    badge = square(load_badge(source))
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for width in BADGE_WIDTHS:
        resized = badge.resize((width, width), Image.LANCZOS)
        path = out_dir / f"badge-{width}.webp"
        resized.save(path, "WEBP", quality=90, method=6)
        written.append(path)

    favicon = out_dir / "favicon.png"
    on_brand_blue(badge, FAVICON_SIZE).save(favicon, "PNG", optimize=True)
    written.append(favicon)

    touch_icon = out_dir / "apple-touch-icon.png"
    on_brand_blue(badge, TOUCH_ICON_SIZE).save(touch_icon, "PNG", optimize=True)
    written.append(touch_icon)

    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    if not args.source.exists():
        print(f"error: source logo not found at {args.source}", file=sys.stderr)
        print("The design/ folder is gitignored; this script needs a local copy.", file=sys.stderr)
        return 1

    for path in build(args.source, args.out):
        print(f"wrote {path.relative_to(REPO_ROOT)} ({path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
