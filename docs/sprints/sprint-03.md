# Sprint 3: Landing page refresh

**Dates:** 2026-09-23 – 2026-10-07
**Roadmap goal:** Catalog data + deploy: database, watch model, admin inventory management, first
deploy.
**Goal as worked:** A landing page the owner is proud to show, with every existing function still
working. Catalog data and deploy move to Sprint 4.

This plan was written on the last day of the sprint. No plan was recorded at sprint planning, so
the roadmap row in `BACKLOG.md` was the only commitment, and the stories it named were never
estimated.

## Stories

| Story | Issue | Points | Status |
| --- | --- | --- | --- |
| Landing page refresh | [#18] | 8 | Done |
| Catalog filters: price range in the service layer | [#20], a task of [#26] | 2 | Done; the route and filter UI come with the catalog page |
| Backlog and sprint board in GitHub Projects | [#19] | 2 | Done; added on the last day |
| Watch data model | [#21] | – | Carried over to Sprint 4 |
| Mark watch status | [#22] | – | Carried over to Sprint 4 |
| Admin inventory management | [#23] | – | Carried over to Sprint 4 |
| Deploy to production | [#24] | – | Carried over to Sprint 4 |

**Completed: 12 points. Carried over: 4 stories, to be estimated at Sprint 4 planning.**

The tests grew from 25 to 35. Each story is one commit on the `sprint-3` branch.

**Lighthouse check.** The refresh's acceptance criteria require mobile Lighthouse performance to
stay at or above 90. The last measurement (99) was taken on 2026-09-22, before the refresh, and the
hero images grew with it. Re-measured on 2026-10-07, after the refresh: still above 90.

## Decisions made this sprint

- **Landing page before the data layer.** The owner chose to bring the storefront to a standard
  worth showing before starting on the database, keeping every core function intact: navigation
  without JavaScript, working links and contact paths, and a green test suite. The data and deploy
  stories move to Sprint 4 unchanged.
- **A new design direction: "bold presentation, quiet voice."** The page moves from Sprint 2's
  quiet white layout to a dark, photo-led one modelled on two reference dealer sites. Navy is now
  the page; the full rules are in [BRAND.md](../BRAND.md).
- **An art-directed hero.** Phones get a 4:5 crop that fades into the page, and landscape screens
  get a 16:9 crop with the watch on the right. A test holds the hero images to a byte budget.
- **The focus ring moves to gold-400**, because `royal-600` only reaches 3.0:1 against the new navy
  page, while gold-400 reaches 9.2:1 or better.
- **Prices are stored as whole US dollars**, with `None` meaning "price on request", and the display
  label is derived from the number. That gives the filters a number to compare. The price filter's
  unit tests are built from equivalence partitions and boundary values.
- **Contact details live in settings** and are exposed to the templates, rather than being
  hard-coded in the footer.
- **A GitHub project board, adopted on the last day.** The course's retrospective asks for a
  screenshot of the board at the start and end of every sprint. Sprints 1–3 were backfilled onto
  the board from their sprint files, so this sprint has an end-of-sprint screenshot but no honest
  start-of-sprint one. The carried-over stories stay in Sprint 3 for that screenshot and move at
  Sprint 4 planning.

## Backlog refinement

- **Internal dashboard** (2026-09-24): planned as a separate frontend on the shared FastAPI
  backend, which narrows the no-JavaScript-framework rule to the storefront. This was committed on
  the `sprint-2` branch after this sprint had started.
- **Stretch stories from the reference sites:** shop by brand, a previously sold archive, a sell or
  source form, and testimonials.
- **Blog epic:** a stretch epic for posts in the owner's own voice.

## Sprint review and retrospective

Kept out of the repository, in `docs/sprints/local/` (gitignored), because they are the owner's
written reflection and feed coursework submissions rather than the codebase.

[#18]: https://github.com/zarekcodes/makarios-luxury/issues/18
[#19]: https://github.com/zarekcodes/makarios-luxury/issues/19
[#20]: https://github.com/zarekcodes/makarios-luxury/issues/20
[#21]: https://github.com/zarekcodes/makarios-luxury/issues/21
[#22]: https://github.com/zarekcodes/makarios-luxury/issues/22
[#23]: https://github.com/zarekcodes/makarios-luxury/issues/23
[#24]: https://github.com/zarekcodes/makarios-luxury/issues/24
[#26]: https://github.com/zarekcodes/makarios-luxury/issues/26
