# Brand

The visual rules for Makarios Luxury. The machine-readable version of this
document is the `@theme` block in `app/static/css/input.css` — if you change a
colour there, change it here too.

## Where the brand comes from

*Makarios* (μακάριος) is Greek for **blessed**. The logo says it literally: a
pair of wings under a gold halo, on a royal blue badge.

That gives the design philosophy: **blessed luxury** — quiet, considered, and
worth keeping, rather than loud. The copy does not need to repeat what the mark
already says. One light touch of the etymology on the page is enough.

## Palette

Every value below was sampled from the logo or derived from it, and every
contrast ratio was measured rather than estimated.

### Blue

`royal-700` is the logo blue. It is unusually useful: AAA as text on white
**and** AAA as a background under white text, so one colour covers headings,
links and button fills.

| Token | Hex | Use | On white | White on it |
| --- | --- | --- | --- | --- |
| `royal-950` | `#02193B` | Dark section band, footer | 17.4 AAA | 17.4 AAA |
| `royal-900` | `#052557` | Headings | 14.9 AAA | 14.9 AAA |
| `royal-800` | `#093A86` | Button hover | 10.7 AAA | 10.7 AAA |
| `royal-700` | `#0F52BA` | **Brand blue.** Links, primary button | 7.15 AAA | 7.15 AAA |
| `royal-600` | `#2B6DD4` | Focus ring | 4.95 AA | 4.95 AA |
| `royal-100` | `#E0EAFA` | Tinted panel | — | background only |
| `royal-50` | `#F2F6FD` | Section wash | — | background only |

### Gold

Gold is the halo. In the logo it is a thin ring, never a filled shape, and the
site follows that.

| Token | Hex | Use | On white | On `royal-950` |
| --- | --- | --- | --- | --- |
| `gold-700` | `#886711` | Gold **text on light backgrounds** | 5.26 AA | — |
| `gold-500` | `#F2B30D` | Rules, borders, icon strokes | 1.87 ✗ | — |
| `gold-400` | `#FAC438` | Halo gold. Accents on dark | 1.61 ✗ | 10.6 AAA |
| `gold-300` | `#FFD770` | Accent text on dark | 1.38 ✗ | 12.3 AAA |

### Neutrals

| Token | Hex | Use | On white |
| --- | --- | --- | --- |
| `ink` | `#0B1220` | Body text | 18.7 AAA |
| `slate-600` | `#4A5568` | Secondary text | 7.53 AAA |
| `slate-500` | `#5B6678` | Captions, metadata | 5.81 AA |
| `silver-400` | `#BFBFBF` | Borders on dark (from the badge ring) | non-text |
| `line` | `#E6E8EE` | 1px borders on light | non-text |
| `cream` | `#FAF8F4` | Alternating section background | — |

## The four gold rules

Gold is the easiest thing here to get wrong, so these are not suggestions.

1. **Never use bright gold as text on white.** `gold-400` is 1.61:1 against
   white — WCAG AA needs 4.5:1. Gold words on a light background use
   `gold-700`.
2. **Bright gold belongs on `royal-950`**, where it reaches 10.6:1. The dark
   trust band is the one place the true halo colour gets to be text.
3. **The focus ring is `royal-600`, never gold.** Non-text indicators need
   3:1; gold does not reach it on white.
4. **Gold is a hairline, not a fill.** Rules, borders, icon strokes, hover
   underlines. Never a button background, never a large area.

## Type

- **Display:** Cormorant Garamond 600, self-hosted at
  `app/static/fonts/`, subset to Latin (~23 KB), `font-display: swap`.
  Licensed under the SIL OFL; the licence ships beside the font.
  Used for `h1`, `h2`, `h3` and the brand name.
- **Body:** the system sans stack. Costs nothing to download and looks native
  on every device.
- **Eyebrow text stays in the sans stack**, which keeps the serif subset
  Latin-only even when Greek characters appear in the copy.

Headings use `clamp()` so they scale smoothly with the viewport instead of
jumping at a breakpoint. There is no separate mobile size to maintain.

## Layout

- Container: `max-w-6xl mx-auto px-5 sm:px-8` — 20px gutters at phone width.
- Section rhythm: `py-16 md:py-24 lg:py-32`. The whitespace *is* the luxury
  signal; resist compressing it.
- Body copy capped at `max-w-[62ch]` for a comfortable line length.
- **Square corners** everywhere except images (`rounded-sm`).
- **No shadows.** Use `border border-line` and space instead. Shadows read as
  software, not as a watch dealer.

## Voice

Quiet, declarative, specific. The trust the site needs is earned by saying
exactly what is true about a watch, including its flaws.

| Do | Don't |
| --- | --- |
| "Box, papers, and service history listed honestly." | "Unbeatable prices!" |
| "If a part isn't original, we say so." | "Luxury, redefined." |
| "Inspected, graded, and documented." | "The finest timepieces in the world." |

No exclamation marks. No superlatives the site cannot back up. The etymology
appears at most twice on a page — once in the hero eyebrow, once in the footer.

## Replacing the logo

The site composes its own lockup from the circle badge plus the name in the
display serif. That is deliberate: the horizontal wordmark in `design/logo/`
has a **solid black background**, not a transparent one, so it cannot sit on a
light header.

To swap in a new logo:

1. Put the new file in `design/logo/`.
2. Run `uv run python scripts/build_brand_assets.py` to regenerate the badge
   sizes and favicons into `app/static/img/brand/`.
3. If you now have a transparent horizontal lockup, replace the contents of
   `app/templates/partials/_brandmark.html` with a single `<img>`. Nothing
   else in the site needs to change.

The originals in `design/` are committed, so a fresh clone can regenerate every derived asset
without hunting for the source files.
