"""Generate stand-in watch photography for the landing page.

Real inventory photos arrive with the catalog in Sprint 3. Until then the page
needs images that behave like the real thing: correct aspect ratio, several
widths so `srcset` has something to choose between, and realistic file sizes so
performance measurements mean something.

The output is committed to the repo, because it is generated *code*, not
uploaded *data*. Regenerate it with:

    uv run python scripts/generate_placeholder_images.py

Output is deterministic: running it twice produces identical bytes, so it never
shows up as noise in a diff.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / "app" / "static" / "img" / "placeholder"

# Portrait 4:5, the standard shape for the catalog grid.
ASPECT = (4, 5)
WATCH_WIDTHS = (400, 800, 1200)
HERO_WIDTHS = (600, 900, 1200)

# Drawn at high resolution and downsampled, which is what keeps the curves
# smooth at 400px instead of visibly jagged.
SUPERSAMPLE = 3

# Brand tokens, mirrored from app/static/css/input.css.
CREAM = (250, 248, 244)
ROYAL_50 = (242, 246, 253)
ROYAL_900 = (5, 37, 87)
ROYAL_700 = (15, 82, 186)
GOLD_500 = (242, 179, 13)
SLATE_500 = (91, 102, 120)
SILVER = (214, 217, 224)


@dataclass(frozen=True)
class Placeholder:
    """One image to generate, in every width."""

    slug: str
    label: str
    case: tuple[int, int, int]
    dial: tuple[int, int, int]
    strap: tuple[int, int, int]


PLACEHOLDERS = (
    Placeholder("watch-01", "Steel chronograph", SILVER, (238, 241, 247), ROYAL_900),
    Placeholder("watch-02", "Gold dress watch", GOLD_500, (252, 250, 243), (74, 52, 28)),
    Placeholder("watch-03", "Titanium diver", (176, 181, 190), ROYAL_700, (32, 38, 50)),
    Placeholder("hero", "Makarios Luxury", GOLD_500, (248, 249, 252), ROYAL_900),
)


def vertical_gradient(
    size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]
):
    """A soft background wash, drawn one row at a time."""
    width, height = size
    image = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(image)

    for y in range(height):
        ratio = y / max(height - 1, 1)
        draw.line(
            [(0, y), (width, y)],
            fill=tuple(round(t + (b - t) * ratio) for t, b in zip(top, bottom, strict=True)),
        )

    return image


def draw_watch(
    draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], spec: Placeholder
) -> None:
    """A simple watch: strap, case, bezel, dial, hands."""
    left, top, right, bottom = box
    cx, cy = (left + right) / 2, (top + bottom) / 2
    case_radius = (right - left) / 2

    strap_width = case_radius * 0.82
    draw.rectangle(
        [cx - strap_width / 2, top - case_radius * 1.45, cx + strap_width / 2, cy],
        fill=spec.strap,
    )
    draw.rectangle(
        [cx - strap_width / 2, cy, cx + strap_width / 2, bottom + case_radius * 1.45],
        fill=spec.strap,
    )

    draw.ellipse([left, top, right, bottom], fill=spec.case)

    bezel = case_radius * 0.09
    draw.ellipse(
        [left + bezel, top + bezel, right - bezel, bottom - bezel],
        fill=spec.dial,
        outline=GOLD_500,
        width=max(round(bezel * 0.55), 1),
    )

    # Hour markers at 12, 3, 6 and 9.
    marker = case_radius * 0.1
    inset = case_radius * 0.76
    for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        mx, my = cx + dx * inset, cy + dy * inset
        draw.ellipse(
            [mx - marker / 2, my - marker / 2, mx + marker / 2, my + marker / 2], fill=ROYAL_900
        )

    hand = max(round(case_radius * 0.055), 1)
    draw.line([cx, cy, cx, cy - case_radius * 0.5], fill=ROYAL_900, width=hand * 2)
    draw.line([cx, cy, cx + case_radius * 0.42, cy + case_radius * 0.2], fill=ROYAL_900, width=hand)
    draw.ellipse([cx - hand, cy - hand, cx + hand, cy + hand], fill=GOLD_500)


def render(spec: Placeholder, width: int) -> Image.Image:
    height = round(width * ASPECT[1] / ASPECT[0])
    scale = SUPERSAMPLE
    big = (width * scale, height * scale)

    image = vertical_gradient(big, CREAM, ROYAL_50)
    draw = ImageDraw.Draw(image)

    case_radius = big[0] * 0.28
    cx, cy = big[0] / 2, big[1] * 0.46
    draw_watch(draw, (cx - case_radius, cy - case_radius, cx + case_radius, cy + case_radius), spec)

    image = image.resize((width, height), Image.LANCZOS)

    # The caption names the file's own width, so you can see which srcset
    # candidate the browser actually chose just by looking at the page.
    caption = f"{spec.label} · {width}px"
    font = ImageFont.load_default(size=max(round(width * 0.035), 10))
    draw = ImageDraw.Draw(image)
    text_width = draw.textlength(caption, font=font)
    draw.text(((width - text_width) / 2, height * 0.88), caption, font=font, fill=SLATE_500)

    return image


def build(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for spec in PLACEHOLDERS:
        widths = HERO_WIDTHS if spec.slug == "hero" else WATCH_WIDTHS
        for width in widths:
            path = out_dir / f"{spec.slug}-{width}.webp"
            render(spec, width).save(path, "WEBP", quality=80, method=6)
            written.append(path)

    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    total = 0
    for path in build(args.out):
        size = path.stat().st_size
        total += size
        print(f"wrote {path.relative_to(REPO_ROOT)} ({size:,} bytes)")
    print(f"\n{total:,} bytes total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
