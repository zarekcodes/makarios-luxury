"""Generate stand-in watch photography for the landing page.

Real photos are on their way. Until they arrive the page needs images that
behave like the real thing: correct aspect ratio, several widths so `srcset`
has something to choose between, and realistic file sizes so performance
measurements mean something. They should also *look* enough like studio shots
that the dark, photo-led layout can be judged honestly, which is why each
watch is lit against a navy backdrop rather than drawn as a flat icon.

The output is committed to the repo, because it is generated *code*, not
uploaded *data*. Regenerate it with:

    uv run python scripts/generate_placeholder_images.py

Output is deterministic: running it twice produces identical bytes, so it never
shows up as noise in a diff. Nothing here is random.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / "app" / "static" / "img" / "placeholder"

# Each shot is drawn once at twice its largest width, then downsampled to every
# width. Downsampling is what keeps the fine lines smooth instead of jagged.
SUPERSAMPLE = 2

RGB = tuple[int, int, int]

# Brand tokens, mirrored from app/static/css/input.css.
ROYAL_950 = (2, 25, 59)
ROYAL_900 = (5, 37, 87)
ROYAL_700 = (15, 82, 186)
GOLD_400 = (250, 196, 56)
GOLD_500 = (242, 179, 13)

# The backdrop: a spotlight a little brighter than royal-900, falling off to a
# navy darker than royal-950 so the page's own background blends into it.
SPOT = (12, 46, 102)
FALLOFF = (1, 10, 28)


@dataclass(frozen=True)
class Metal:
    """A polished metal, as the two ends of its reflection."""

    shadow: RGB
    light: RGB


STEEL = Metal(shadow=(88, 97, 112), light=(240, 242, 247))
GOLD = Metal(shadow=(120, 84, 14), light=(255, 228, 146))
TITANIUM = Metal(shadow=(78, 85, 98), light=(186, 192, 203))


@dataclass(frozen=True)
class Watch:
    """What to draw. `kind` picks the layout: chronograph, dress or diver."""

    kind: str
    brand: str
    subtitle: str
    metal: Metal
    dial: RGB
    dial_sheen: RGB
    ink: RGB  # dial printing and minute track
    strap: RGB
    stitching: RGB | None


@dataclass(frozen=True)
class Shot:
    """One image file family: a watch, framed, at several widths."""

    slug: str
    watch: Watch
    aspect: tuple[int, int]
    widths: tuple[int, ...]
    centre: tuple[float, float]  # watch centre, as fractions of width and height
    case_radius: float  # as a fraction of the image width
    tilt: float = 0.0  # degrees, positive is anticlockwise
    halo: bool = False


CHRONOGRAPH = Watch(
    kind="chronograph",
    brand="AURELIAN",
    subtitle="CHRONOGRAPH",
    metal=STEEL,
    dial=(226, 230, 236),
    dial_sheen=(250, 251, 253),
    ink=ROYAL_900,
    strap=ROYAL_900,
    stitching=(154, 170, 196),
)
DRESS = Watch(
    kind="dress",
    brand="CALLOWAY",
    subtitle="AUTOMATIC",
    metal=GOLD,
    dial=(236, 226, 204),
    dial_sheen=(252, 247, 236),
    ink=(98, 76, 40),
    strap=(74, 48, 26),
    stitching=(196, 170, 128),
)
DIVER = Watch(
    kind="diver",
    brand="NORVELL",
    subtitle="300 M",
    metal=TITANIUM,
    dial=(9, 52, 132),
    dial_sheen=(52, 116, 222),
    ink=(226, 234, 248),
    strap=(30, 35, 46),
    stitching=None,
)
# The hero piece: gold on navy leather, the brand's own two colours.
HERO_PIECE = Watch(
    kind="dress",
    brand="CALLOWAY",
    subtitle="AUTOMATIC",
    metal=GOLD,
    dial=(222, 216, 204),
    dial_sheen=(250, 248, 242),
    ink=(98, 76, 40),
    strap=ROYAL_900,
    stitching=(176, 150, 96),
)

CARD = {"aspect": (4, 5), "widths": (400, 800, 1200), "centre": (0.5, 0.47), "case_radius": 0.3}

SHOTS = (
    Shot("watch-01", CHRONOGRAPH, **CARD),
    Shot("watch-02", DRESS, **CARD),
    Shot("watch-03", DIVER, **CARD),
    # Portrait screens: shown at its natural shape across the top of the hero,
    # fading into the navy page. The text starts below the watch, which the
    # hero's top padding in home.html (90vw) assumes ends about 70% of the way down.
    Shot(
        "hero-portrait",
        HERO_PIECE,
        aspect=(4, 5),
        widths=(600, 900, 1200),
        centre=(0.5, 0.4),
        case_radius=0.3,
        tilt=-8,
        halo=True,
    ),
    # Landscape screens: the watch sits in the right quarter, leaving the left
    # side dark for the text even on a 1024px tablet.
    Shot(
        "hero-wide",
        HERO_PIECE,
        aspect=(16, 9),
        widths=(960, 1440, 1920),
        centre=(0.74, 0.5),
        case_radius=0.14,
        tilt=-12,
        halo=True,
    ),
)


# ---- Small geometry and colour helpers -------------------------------------


def mix(a: RGB, b: RGB, t: float) -> RGB:
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b, strict=True))


def rgba(colour: RGB, alpha: int = 255) -> tuple[int, int, int, int]:
    return (*colour, alpha)


def point(cx: float, cy: float, r: float, theta: float) -> tuple[float, float]:
    """A point at radius r and clock angle theta (degrees, clockwise from 12)."""
    rad = math.radians(theta)
    return cx + r * math.sin(rad), cy - r * math.cos(rad)


def radial_bar(
    cx: float, cy: float, r0: float, r1: float, width: float, theta: float
) -> list[tuple[float, float]]:
    """A rectangle pointing out from the centre: an index, a tick, a pusher."""
    rad = math.radians(theta)
    px, py = math.cos(rad) * width / 2, math.sin(rad) * width / 2
    (x0, y0), (x1, y1) = point(cx, cy, r0, theta), point(cx, cy, r1, theta)
    return [(x0 - px, y0 - py), (x1 - px, y1 - py), (x1 + px, y1 + py), (x0 + px, y0 + py)]


def disc(cx: float, cy: float, r: float) -> tuple[float, float, float, float]:
    return (cx - r, cy - r, cx + r, cy + r)


def sheen(theta: float, phase: float, sharpness: float) -> float:
    """How brightly a surface at this angle catches the light, 0 to 1.

    Polished metal and sunburst dials both reflect in two opposite lobes, which
    is what cos(2θ) describes. Raising it to a power narrows the highlights.
    """
    return ((1 + math.cos(math.radians(2 * (theta - phase)))) / 2) ** sharpness


def conic_disc(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    r: float,
    dark: RGB,
    light: RGB,
    phase: float = 315,
    sharpness: float = 1.0,
) -> None:
    """Fill a disc whose colour turns with the angle, one degree at a time."""
    for step in range(360):
        colour = mix(dark, light, sheen(step, phase, sharpness))
        # PIL measures from 3 o'clock; the half-degree overlap hides seams.
        draw.pieslice(disc(cx, cy, r), step - 90, step - 88.5, fill=rgba(colour))


def profile_strip(size: tuple[int, int], dark: RGB, light: RGB) -> Image.Image:
    """A band that is light down its middle and dark at both edges: a strap."""
    ramp = Image.new("L", (256, 1))
    ramp.putdata([round(255 * math.sin(math.pi * x / 255) ** 1.5) for x in range(256)])
    return ImageOps.colorize(ramp.resize(size, Image.BICUBIC), dark, light).convert("RGBA")


def spaced_text(
    draw: ImageDraw.ImageDraw,
    centre: tuple[float, float],
    text: str,
    font: ImageFont.FreeTypeFont,
    tracking: float,
    fill: RGB,
) -> None:
    """Letter-spaced text centred on a point, the way dial printing is set."""
    widths = [draw.textlength(char, font=font) for char in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = centre[0] - total / 2
    for char, width in zip(text, widths, strict=True):
        draw.text((x, centre[1]), char, font=font, fill=rgba(fill), anchor="lm")
        x += width + tracking


# ---- The watch ---------------------------------------------------------------


def draw_strap(layer: Image.Image, watch: Watch, cx: float, cy: float, r: float) -> None:
    width = round(r * 0.98)
    left = round(cx - width / 2)
    dark, light = mix(watch.strap, (0, 0, 0), 0.5), mix(watch.strap, (255, 255, 255), 0.1)

    for top, bottom in ((0, round(cy - r * 0.5)), (round(cy + r * 0.5), layer.height)):
        strip = profile_strip((width, bottom - top), dark, light)
        layer.alpha_composite(strip, (left, top))

    draw = ImageDraw.Draw(layer)
    if watch.stitching is None:
        # Rubber: two moulded channels instead of stitching.
        for dx in (-0.2, 0.2):
            x = cx + r * dx
            for top, bottom in ((0, cy - r * 1.2), (cy + r * 1.2, layer.height)):
                draw.line([(x, top), (x, bottom)], fill=rgba(dark), width=round(r * 0.02))
        return

    # Stitching: short dashes inset from each edge.
    dash, gap, inset = r * 0.055, r * 0.035, r * 0.075
    for x in (left + inset, left + width - inset):
        for top, bottom in ((0, cy - r * 1.22), (cy + r * 1.22, layer.height)):
            y = top
            while y < bottom:
                draw.line(
                    [(x, y), (x, min(y + dash, bottom))],
                    fill=rgba(watch.stitching),
                    width=max(round(r * 0.014), 1),
                )
                y += dash + gap


def draw_case(draw: ImageDraw.ImageDraw, watch: Watch, cx: float, cy: float, r: float) -> None:
    metal = watch.metal
    strap_half = r * 0.49
    lug = r * 0.15

    # Four lugs, drawn first so the case covers their roots. Each tapers
    # towards its tip and is split along its length into a lit face and a
    # shaded one, which is what makes it read as a bevel rather than a bar.
    for side in (-1, 1):
        for end in (-1, 1):
            inner = cx + side * strap_half
            root, tip = cy + end * r * 0.55, cy + end * r * 1.12
            outer_root, outer_tip = inner + side * lug * 1.35, inner + side * lug * 0.8
            ridge_root, ridge_tip = inner + side * lug * 0.6, inner + side * lug * 0.4
            lit = mix(metal.shadow, metal.light, 0.85 if side < 0 else 0.55)
            shaded = mix(metal.shadow, metal.light, 0.45 if side < 0 else 0.15)
            draw.polygon(
                [(inner, root), (ridge_root, root), (ridge_tip, tip), (inner, tip)], fill=rgba(lit)
            )
            draw.polygon(
                [(ridge_root, root), (outer_root, root), (outer_tip, tip), (ridge_tip, tip)],
                fill=rgba(shaded),
            )

    # Crown at 3 o'clock, with grip lines.
    crown_h = r * (0.3 if watch.kind == "diver" else 0.22)
    crown = (cx + r * 0.92, cy - crown_h / 2, cx + r * 1.12, cy + crown_h / 2)
    draw.rounded_rectangle(crown, radius=r * 0.03, fill=rgba(mix(metal.shadow, metal.light, 0.6)))
    for i in range(1, 6):
        y = crown[1] + crown_h * i / 6
        draw.line([(crown[0] + r * 0.06, y), (crown[2], y)], fill=rgba(metal.shadow), width=2)

    if watch.kind == "chronograph":
        for theta in (60, 120):
            draw.polygon(
                radial_bar(cx, cy, r * 0.9, r * 1.1, r * 0.13, theta),
                fill=rgba(mix(metal.shadow, metal.light, 0.55)),
            )

    # The case itself, then a bezel whose highlight is turned the other way,
    # which reads as a polished step between the two.
    conic_disc(draw, cx, cy, r, metal.shadow, metal.light, phase=315, sharpness=2)
    conic_disc(draw, cx, cy, r * 0.94, metal.shadow, metal.light, phase=45, sharpness=3)
    draw.ellipse(disc(cx, cy, r), outline=rgba(mix(metal.shadow, (0, 0, 0), 0.4)), width=3)


def draw_diver_bezel(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float) -> None:
    outer, inner = r * 0.9, r * 0.74
    conic_disc(draw, cx, cy, outer, ROYAL_950, (22, 58, 118), phase=315, sharpness=2)
    for minute in range(60):
        theta = minute * 6
        if minute == 0:
            continue
        if minute % 5 == 0:
            draw.polygon(
                radial_bar(cx, cy, outer * 0.86, outer * 0.97, r * 0.035, theta),
                fill=rgba((226, 234, 248)),
            )
        elif minute < 15:
            draw.polygon(
                radial_bar(cx, cy, outer * 0.92, outer * 0.97, r * 0.012, theta),
                fill=rgba((196, 208, 228)),
            )
    # The gold pip at 12, the brand's halo colour doing a diver's job.
    tip = point(cx, cy, outer * 0.84, 0)
    draw.polygon(
        [(tip[0], tip[1]), (cx - r * 0.07, cy - outer * 0.98), (cx + r * 0.07, cy - outer * 0.98)],
        fill=rgba(GOLD_400),
    )
    draw.ellipse(disc(cx, cy, inner + r * 0.015), fill=rgba((12, 16, 26)))


def draw_dial(
    layer: Image.Image, watch: Watch, cx: float, cy: float, r: float, dial_r: float
) -> None:
    draw = ImageDraw.Draw(layer)
    # The rehaut: a dark ring where the dial meets the case, for depth.
    draw.ellipse(
        disc(cx, cy, dial_r + r * 0.025), fill=rgba(mix(watch.metal.shadow, (0, 0, 0), 0.5))
    )
    conic_disc(draw, cx, cy, dial_r, watch.dial, watch.dial_sheen, phase=315, sharpness=1.4)

    # Minute track.
    if watch.kind != "diver":
        for minute in range(60):
            if minute % 5:
                draw.polygon(
                    radial_bar(cx, cy, dial_r * 0.93, dial_r * 0.98, r * 0.008, minute * 6),
                    fill=rgba(watch.ink),
                )

    if watch.kind == "chronograph":
        for theta in (90, 270):
            sx, sy = point(cx, cy, dial_r * 0.42, theta)
            sr = dial_r * 0.24
            draw.ellipse(
                disc(sx, sy, sr), fill=rgba(ROYAL_900), outline=rgba((180, 188, 204)), width=3
            )
            for tick in range(12):
                draw.polygon(
                    radial_bar(sx, sy, sr * 0.8, sr * 0.95, r * 0.01, tick * 30),
                    fill=rgba((214, 222, 236)),
                )
            draw.polygon(
                radial_bar(sx, sy, 0, sr * 0.78, r * 0.016, 135 + theta), fill=rgba((236, 240, 246))
            )
            draw.ellipse(disc(sx, sy, r * 0.018), fill=rgba((236, 240, 246)))

    # Hour indices: two-tone applied batons that catch the light on one side.
    metal = watch.metal if watch.kind != "diver" else STEEL
    for hour in range(12):
        theta = hour * 30
        if watch.kind == "chronograph" and hour in (3, 9):
            continue
        if watch.kind == "diver" and hour % 3:
            x, y = point(cx, cy, dial_r * 0.8, theta)
            draw.ellipse(
                disc(x, y, r * 0.055),
                fill=rgba((236, 238, 228)),
                outline=rgba(metal.light),
                width=3,
            )
            continue

        width = r * (0.06 if watch.kind == "diver" else 0.045)
        r0, r1 = dial_r * (0.66 if watch.kind == "diver" else 0.7), dial_r * 0.88
        bars = [0] if hour else [-width * 0.8, width * 0.8]
        for offset in bars:
            bx, by = point(cx, cy, offset, theta + 90)
            bar = radial_bar(bx, by, r0, r1, width, theta)
            mid0 = ((bar[0][0] + bar[3][0]) / 2, (bar[0][1] + bar[3][1]) / 2)
            mid1 = ((bar[1][0] + bar[2][0]) / 2, (bar[1][1] + bar[2][1]) / 2)
            draw.polygon([bar[0], bar[1], mid1, mid0], fill=rgba(metal.light))
            draw.polygon([mid0, mid1, bar[2], bar[3]], fill=rgba(metal.shadow))

    # Dial printing.
    font = ImageFont.load_default(size=max(round(r * 0.085), 8))
    small = ImageFont.load_default(size=max(round(r * 0.052), 6))
    brand_y = cy - dial_r * (0.36 if watch.kind == "chronograph" else 0.4)
    spaced_text(draw, (cx, brand_y), watch.brand, font, r * 0.02, watch.ink)
    subtitle_y = cy + dial_r * (0.58 if watch.kind == "chronograph" else 0.4)
    subtitle_ink = GOLD_400 if watch.kind == "diver" else watch.ink
    spaced_text(draw, (cx, subtitle_y), watch.subtitle, small, r * 0.016, subtitle_ink)


def draw_hands(
    layer: Image.Image, watch: Watch, cx: float, cy: float, r: float, dial_r: float
) -> None:
    """Hands at 10:09, the angle watch photography has used for a century."""
    if watch.kind == "diver":
        light, dark = (246, 247, 242), (178, 184, 192)
    else:
        light, dark = watch.metal.light, watch.metal.shadow

    def dauphine(length: float, width: float, theta: float) -> list[list[tuple[float, float]]]:
        back = point(cx, cy, -length * 0.1, theta)
        tip = point(cx, cy, length, theta)
        base = point(cx, cy, length * 0.14, theta)
        rad = math.radians(theta)
        px, py = math.cos(rad) * width / 2, math.sin(rad) * width / 2
        left, right = (base[0] - px, base[1] - py), (base[0] + px, base[1] + py)
        return [[back, left, tip], [back, tip, right]]

    hands = [
        dauphine(dial_r * 0.56, r * 0.085, (10 + 9 / 60) * 30),
        dauphine(dial_r * 0.86, r * 0.068, 9 * 6),
    ]
    seconds_theta = 36 * 6
    seconds = radial_bar(cx, cy, -dial_r * 0.2, dial_r * 0.92, r * 0.012, seconds_theta)
    seconds_colour = (
        GOLD_500 if watch.kind == "diver" else (ROYAL_700 if watch.kind == "chronograph" else dark)
    )

    # A soft shadow under the hands lifts them off the dial.
    shadow = Image.new("L", layer.size, 0)
    shadow_draw = ImageDraw.Draw(shadow)
    offset = (r * 0.02, r * 0.035)
    for hand in hands:
        for half in hand:
            shadow_draw.polygon([(x + offset[0], y + offset[1]) for x, y in half], fill=110)
    shadow_draw.polygon([(x + offset[0], y + offset[1]) for x, y in seconds], fill=90)
    shadow = shadow.filter(ImageFilter.GaussianBlur(r * 0.02))
    layer.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", layer.size).split(), shadow)))

    draw = ImageDraw.Draw(layer)
    for hand in hands:
        draw.polygon(hand[0], fill=rgba(light))
        draw.polygon(hand[1], fill=rgba(dark))
    draw.polygon(seconds, fill=rgba(seconds_colour))
    cw = point(cx, cy, -dial_r * 0.14, seconds_theta)
    draw.ellipse(disc(*cw, r * 0.03), fill=rgba(seconds_colour))
    draw.ellipse(disc(cx, cy, r * 0.045), fill=rgba(dark))
    draw.ellipse(disc(cx, cy, r * 0.025), fill=rgba(light))


def draw_glare(layer: Image.Image, cx: float, cy: float, dial_r: float) -> None:
    """A faint crescent of reflected light across the crystal."""
    mask = Image.new("L", layer.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(disc(cx, cy, dial_r), fill=255)
    draw.ellipse(disc(cx + dial_r * 0.22, cy + dial_r * 0.3, dial_r * 1.05), fill=0)
    mask = mask.filter(ImageFilter.GaussianBlur(dial_r * 0.06)).point(lambda v: v * 30 // 255)

    clip = Image.new("L", layer.size, 0)
    ImageDraw.Draw(clip).ellipse(disc(cx, cy, dial_r), fill=255)
    mask = ImageChops.multiply(mask, clip)

    white = Image.new("RGBA", layer.size, (255, 255, 255, 0))
    white.putalpha(mask)
    layer.alpha_composite(white)


def render_watch(watch: Watch, r: float, strap_half: float) -> Image.Image:
    """The whole watch, upright, centred on a transparent layer."""
    size = (math.ceil(r * 2.6), math.ceil(strap_half * 2))
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    cx, cy = size[0] / 2, size[1] / 2

    draw_strap(layer, watch, cx, cy, r)
    draw = ImageDraw.Draw(layer)
    draw_case(draw, watch, cx, cy, r)

    if watch.kind == "diver":
        draw_diver_bezel(draw, cx, cy, r)
        dial_r = r * 0.72
    else:
        dial_r = r * (0.86 if watch.kind == "chronograph" else 0.88)

    draw_dial(layer, watch, cx, cy, r, dial_r)
    draw_hands(layer, watch, cx, cy, r, dial_r)
    draw_glare(layer, cx, cy, dial_r)
    return layer


# ---- Composition ---------------------------------------------------------------


def backdrop(size: tuple[int, int], focus: tuple[float, float], radius: float) -> Image.Image:
    """A navy studio backdrop with a soft spotlight behind the watch."""
    # Pillow's radial gradient reaches only 181 at the edge of its circle (255
    # is the corner), so rescale it: full falloff exactly at `radius`, eased so
    # the light fades out rather than ending at a visible edge.
    gradient = Image.radial_gradient("L").point(lambda v: round(255 * min(v / 181, 1) ** 0.8))
    gradient = gradient.resize((round(radius * 2),) * 2, Image.BICUBIC)
    mask = Image.new("L", size, 255)
    mask.paste(gradient, (round(focus[0] - radius), round(focus[1] - radius)))
    return Image.composite(Image.new("RGB", size, FALLOFF), Image.new("RGB", size, SPOT), mask)


def render(shot: Shot) -> Image.Image:
    """Draw the shot once, at twice its largest width."""
    width = max(shot.widths) * SUPERSAMPLE
    height = round(width * shot.aspect[1] / shot.aspect[0])
    cx, cy = width * shot.centre[0], height * shot.centre[1]
    r = width * shot.case_radius

    image = backdrop((width, height), (cx, cy - r * 0.2), max(width, height) * 0.62).convert("RGBA")

    if shot.halo:
        # A thin gold ring behind the watch: the logo's halo, as a hairline.
        halo = Image.new("RGBA", image.size, (0, 0, 0, 0))
        ImageDraw.Draw(halo).ellipse(
            disc(cx, cy, r * 1.62), outline=rgba(GOLD_400, 120), width=max(round(r * 0.012), 2)
        )
        image.alpha_composite(halo.filter(ImageFilter.GaussianBlur(r * 0.004)))

    # The strap must run off both edges of the frame even once tilted.
    strap_half = max(cy, height - cy) / math.cos(math.radians(shot.tilt)) + r
    watch = render_watch(shot.watch, r, strap_half)
    if shot.tilt:
        watch = watch.rotate(shot.tilt, resample=Image.BICUBIC, expand=True)
    origin = (round(cx - watch.width / 2), round(cy - watch.height / 2))

    shadow_mask = Image.new("L", image.size, 0)
    shadow_mask.paste(
        watch.getchannel("A"), (origin[0] + round(r * 0.05), origin[1] + round(r * 0.1))
    )
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(r * 0.08)).point(
        lambda v: v * 150 // 255
    )
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow.putalpha(shadow_mask)
    image.alpha_composite(shadow)

    image.alpha_composite(watch, origin)
    return image.convert("RGB")


def build(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for shot in SHOTS:
        master = render(shot)
        for width in shot.widths:
            height = round(width * shot.aspect[1] / shot.aspect[0])
            path = out_dir / f"{shot.slug}-{width}.webp"
            master.resize((width, height), Image.LANCZOS).save(path, "WEBP", quality=80, method=6)
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
        shown = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        print(f"wrote {shown} ({size:,} bytes)")
    print(f"\n{total:,} bytes total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
