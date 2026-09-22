# Sprint 2: Landing page MVP

**Dates:** 2026-09-22 – 2026-10-05
**Sprint goal:** A polished, responsive landing page built on static placeholder content, on a
Tailwind + htmx toolchain that CI verifies.

## Committed stories

| Story | Points | Status |
| --- | --- | --- |
| Frontend tooling (Tailwind, htmx, design tokens, brand assets) | 5 | Done |
| Placeholder watch imagery | 2 | Done |
| Site header and navigation | 3 | Done |
| Hero section | 3 | Done |
| Featured watches | 3 | Done |
| Trust section | 2 | Done |
| Footer | 2 | Done |

**Committed: 20 points. Completed: 20.**

Each story is one commit on the `sprint-2` branch, so `git log` reads story by story.

## Design decisions made this sprint

Recorded here because they were made during the sprint rather than being inherited from the
backlog. The full rules live in [BRAND.md](../BRAND.md).

- **Design philosophy: "blessed luxury."** Quiet and editorial rather than loud. Royal blue and
  gold on white, generous whitespace, large display serif headings, square corners, no shadows.
- **Palette sampled from the logo**, not invented. The brand blue is `#0F52BA`, which happens to be
  AAA both as text on white and as a background under white text.
- **Gold is constrained.** The halo gold fails contrast badly as text on white (1.61:1), so it is
  decorative on light backgrounds and only becomes text on the dark `royal-950` band.
- **The generated stylesheet is committed.** The deploy target has no Node and no Tailwind binary,
  so an uncommitted `app.css` would ship an unstyled site. A CI job rebuilds and byte-compares it.
- **The mobile menu uses native `<details>`/`<summary>`**, opening a panel anchored under the
  header rather than a full-screen overlay. It works with JavaScript disabled, and because it is
  not a modal it needs no focus trap, Escape handler or scroll lock.
- **No `hx-boost` yet.** There is no second page to navigate to; revisit in Sprint 4.

## Sprint review

_What shipped:_

- **A complete landing page** at `/`: header with navigation, hero, three featured watches, a trust
  section and a footer. It works at 400px and on desktop.
- **The frontend toolchain.** Tailwind CSS via the standalone CLI (no Node.js), built by
  `scripts/tailwind.sh` with the version pinned in one place, and htmx vendored locally rather than
  loaded from a CDN.
- **A brand design system.** Colours sampled from the logo rather than guessed: the brand blue
  `#0F52BA` is AAA-contrast both as text on white and as a background under white text. Recorded as
  design tokens in `input.css` and as usage rules in `docs/BRAND.md`.
- **Generated placeholder imagery.** `scripts/generate_placeholder_images.py` produces twelve WebP
  files at three widths each, so `srcset` is exercised for real before there is any real
  photography.
- **A mobile menu that works with JavaScript disabled**, built on native `<details>`/`<summary>`.
- **25 tests**, covering asset delivery, link integrity, image dimensions, and the no-JavaScript
  navigation.
- **A new CI job** that rebuilds the stylesheet and fails if the committed copy is out of date.

_Bug found and fixed during the sprint:_ Tailwind's automatic file detection was scanning the whole
project, not just the templates, so the stylesheet included rules harvested from Markdown code
examples and would not rebuild identically from a clean checkout. Fixed with `source(none)`; the
stylesheet shrank from 20.0 KB to 15.2 KB.

_Page weight, first load at phone width:_ ~140 KB uncompressed, including a 16 KB (gzipped) htmx
and a 23 KB subset font.

_Lighthouse mobile performance score:_ _(run DevTools → Lighthouse → Mobile and record it here)_

## Retrospective

**What went well:**

**What didn't:**

**One change for Sprint 3:**
