# Brand

The visual rules for Makarios Luxury. The machine-readable version of this
document is the `@theme` block in `app/static/css/input.css` — if you change a
colour there, change it here too.

## Where the brand comes from

*Makarios* (μακάριος) is Greek for **blessed**. The logo says it literally: a
pair of wings under a gold halo, on a royal blue badge.

That gives the design philosophy: **bold presentation, quiet voice.**

- **The watches are loud.** Photography leads, full-bleed and large, on a navy
  page that makes gold and steel glow. A buyer should see a watch worth wanting
  before they read a word.
- **The words are quiet.** Say plainly what Makarios sells, then get out of the
  way. The trust the site needs is earned by being specific, not by shouting
  (see Voice below).
- **The next step is obvious.** Every screen offers one clear thing to do:
  shop the collection, or ask about a watch.

The copy does not need to repeat what the mark already says. One light touch of
the etymology on the page is enough.

## Palette

Every value below was sampled from the logo or derived from it, and every
contrast ratio was measured rather than estimated.

### Blue

`royal-700` is the logo blue. It is unusually useful: AAA as text on white
**and** AAA as a background under white text, so on a light page one colour
covers headings, links and button fills. The site itself is now navy: the
darkest two blues are the surfaces, and the brand blue stays in the logo.

| Token | Hex | Use | On white | White on it |
| --- | --- | --- | --- | --- |
| `royal-950` | `#02193B` | **The page.** Header, hero, featured watches, contact band, footer | 17.4 AAA | 17.4 AAA |
| `royal-900` | `#052557` | The alternate band (trust section), image frames | 14.9 AAA | 14.9 AAA |
| `royal-800` | `#093A86` | Button hover on light | 10.7 AAA | 10.7 AAA |
| `royal-700` | `#0F52BA` | **Brand blue.** The logo's badge; links and buttons on light | 7.15 AAA | 7.15 AAA |
| `royal-600` | `#2B6DD4` | Reserved. It was the focus ring on white; see gold rule 3 | 4.95 AA | 4.95 AA |
| `royal-100` | `#E0EAFA` | **Body text on navy**; button hover | — | — |
| `royal-50` | `#F2F6FD` | Section wash on light | — | background only |

### Gold

Gold is the halo. In the logo it is a thin ring, never a filled shape, and the
site follows that.

| Token | Hex | Use | On white | On `royal-950` |
| --- | --- | --- | --- | --- |
| `gold-700` | `#886711` | Gold **text on light backgrounds** | 5.26 AA | — |
| `gold-500` | `#F2B30D` | Rules, borders, icon strokes | 1.87 ✗ | — |
| `gold-400` | `#FAC438` | Halo gold. Eyebrows, outlines, focus ring on navy | 1.61 ✗ | 10.8 AAA |
| `gold-300` | `#FFD770` | Prices and accent text on navy | 1.38 ✗ | 12.6 AAA |

### Neutrals

| Token | Hex | Use | On white |
| --- | --- | --- | --- |
| `ink` | `#0B1220` | Body text | 18.7 AAA |
| `slate-600` | `#4A5568` | Secondary text | 7.53 AAA |
| `slate-500` | `#5B6678` | Captions, metadata | 5.81 AA |
| `silver-400` | `#BFBFBF` | Secondary text on navy; borders (from the badge ring) | non-text |
| `line` | `#E6E8EE` | 1px borders on light | non-text |
| `cream` | `#FAF8F4` | Background on light pages | — |

### On navy

Navy is the page, so these are the pairs the site actually uses. Measured with
the WCAG 2 formula; AA needs 4.5:1 for body text and 3:1 for large text and for
non-text indicators such as borders and focus rings.

| Foreground | Use | On `royal-950` | On `royal-900` |
| --- | --- | --- | --- |
| white | Headings, button text, primary button fill | 17.4 AAA | 14.9 AAA |
| `royal-100` | Body text | 14.4 AAA | 12.3 AAA |
| `gold-300` | Prices, the hero eyebrow | 12.6 AAA | 10.8 AAA |
| `gold-400` | Eyebrows, focus ring, outline buttons | 10.8 AAA | 9.2 AAA |
| `silver-400` | Secondary text: card labels | 9.5 AAA | 8.1 AAA |
| `royal-600` | *Not used on navy* | 3.5 | 3.0 |

`royal-950` text on the white primary button measures 17.4, AAA.

## The four gold rules

Gold is the easiest thing here to get wrong, so these are not suggestions.

1. **Never use bright gold as text on white.** `gold-400` is 1.61:1 against
   white — WCAG AA needs 4.5:1. Gold words on a light background use
   `gold-700`.
2. **Bright gold belongs on navy**: `royal-950` or `royal-900`, where it
   measures 9–12:1. Now that navy is the page, that is most of the site:
   eyebrows, prices and the outline button are all gold.
3. **On navy, the focus ring is `gold-400`.** Non-text indicators need 3:1.
   The old `royal-600` ring manages only 3.0:1 on `royal-900`, the bare
   minimum; gold reaches 9.2. On a light background the ring would have to
   go back to `royal-600`, because there gold falls below 3:1.
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
- **Navy is the page.** Sections sit on `royal-950`; the trust section steps
  up to `royal-900` so the page still has a rhythm of bands. Separate with
  space and 1px `white/15` or gold hairlines, not with colour blocks.
- Section rhythm: `py-16 md:py-24 lg:py-32`. The whitespace is still part of
  the luxury signal; resist compressing it.
- Body copy capped at `max-w-[62ch]` for a comfortable line length.
- **Square corners** everywhere except images (`rounded-sm`).
- **No interface shadows.** Use borders and space instead. Shadows on cards
  and buttons read as software, not as a watch dealer. The shadow a watch
  casts in its own photograph is fine: that is lighting, not interface.

### Buttons on navy

| Role | Style | Example |
| --- | --- | --- |
| Primary, one per screen | White fill, `royal-950` text, hover `royal-100` | Shop the collection |
| Secondary | 1px `gold-400` outline, white text, hover `white/10` | Ask about a watch |
| Inline | White text link with an arrow, underline on hover | Inquire &rarr; |

### Text over photographs

The hero lays its words over a photograph. That is only allowed on a
`royal-950` gradient that sits between photo and text, and the contrast is
checked against the photograph, not assumed:

- The gradient runs from solid navy behind the text to transparent over the
  watch, so the watch stays bright and the words stay legible.
- Measure the worst pixel under each line of text at common screen sizes. At
  the time of writing, with the stand-in images: headline 8.3:1 or better,
  body text 10:1 or better, the small gold eyebrow 4.5:1 or better.
- Re-check whenever the hero photograph changes.

## Voice

Quiet, declarative, specific. The trust the site needs is earned by saying
exactly what is true about a watch, including its flaws.

| Do | Don't |
| --- | --- |
| "Box, papers, and service history listed honestly." | "Unbeatable prices!" |
| "If a part isn't original, we say so." | "Luxury, redefined." |
| "Inspected, graded, and documented." | "The finest timepieces in the world." |
| "Ask about any watch." | "Contact us today!" |
| "Selling a watch? We buy those too." | "We pay top dollar for your watch!" |

No exclamation marks. No superlatives the site cannot back up. The etymology
appears at most twice on a page — once in the hero eyebrow, once in the footer.

## Photography

The layout is built around photographs, so the photographs have a brief.

- **Dark, even backgrounds.** Navy or near-black makes the watch the brightest
  thing on the page and lets the image melt into the page around it.
- **The hero needs two crops of the same shot**, because phones and laptops
  frame it differently:
  - `hero-portrait`, 4:5, with the watch in the upper part of the frame and
    nothing important below about 70% of the height. The headline sits there.
  - `hero-wide`, 16:9, with the watch in the right third and the left half
    empty. The headline sits there.
- **Card photos are 4:5**, the watch centred.
- **Weight budget:** each hero file stays under 150 KB (a test enforces it).
  An unedited camera file is several megabytes; resize and export as WebP.

Until real photography arrives, `scripts/generate_placeholder_images.py` draws
stand-ins that follow this brief. To swap a real photo in, export it at the same
widths with the same names (`hero-portrait-600.webp` and so on), or point the
`name=` in `pages/home.html` and `partials/watch_card.html` at the new files.

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
