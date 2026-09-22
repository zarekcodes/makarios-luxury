# Sprint 2: Landing page MVP

**Dates:** 2026-09-22 – 2026-10-05
**Sprint goal:** A polished, responsive landing page built on static placeholder content, on a
Tailwind + htmx toolchain that CI verifies.

## Committed stories

| Issue | Story | Points | Status |
| --- | --- | --- | --- |
| # | Frontend tooling (Tailwind, htmx, design tokens, brand assets) | 5 | |
| # | Placeholder watch imagery | 2 | |
| # | Site header and navigation | 3 | |
| # | Hero section | 3 | |
| # | Featured watches | 3 | |
| # | Trust section | 2 | |
| # | Footer | 2 | |

**Committed: 20 points.**

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
- **The mobile menu uses native `<details>`/`<summary>`** and pushes content down rather than
  covering it, which keeps it working with JavaScript disabled and avoids needing a focus trap.
- **No `hx-boost` yet.** There is no second page to navigate to; revisit in Sprint 4.

## Sprint review

_What was demoed / what shipped:_

_Lighthouse mobile performance score:_

## Retrospective

**What went well:**

**What didn't:**

**One change for Sprint 3:**
