# Sprint 2: Landing page MVP

**Dates:** 2026-09-22 (planned through 10-05; Sprint 3 began on 09-23)
**Sprint goal:** A polished, responsive landing page built on static placeholder content, on a
Tailwind + htmx toolchain that CI verifies.

## Committed stories

| Story | Issue | Points | Status |
| --- | --- | --- | --- |
| Frontend tooling (Tailwind, htmx, design tokens, brand assets) | [#11] | 5 | Done |
| Placeholder watch imagery | [#12] | 2 | Done |
| Site header and navigation | [#13] | 3 | Done |
| Hero section | [#14] | 3 | Done |
| Featured watches | [#15] | 3 | Done |
| Trust section | [#16] | 2 | Done |
| Footer | [#17] | 2 | Done |

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

## Sprint review and retrospective

Kept out of the repository, in `docs/sprints/local/` (gitignored), because they are the owner's
written reflection and feed coursework submissions rather than the codebase.

[#11]: https://github.com/zarekcodes/makarios-luxury/issues/11
[#12]: https://github.com/zarekcodes/makarios-luxury/issues/12
[#13]: https://github.com/zarekcodes/makarios-luxury/issues/13
[#14]: https://github.com/zarekcodes/makarios-luxury/issues/14
[#15]: https://github.com/zarekcodes/makarios-luxury/issues/15
[#16]: https://github.com/zarekcodes/makarios-luxury/issues/16
[#17]: https://github.com/zarekcodes/makarios-luxury/issues/17
