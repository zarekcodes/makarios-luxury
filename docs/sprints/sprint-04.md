# Sprint 4: Catalog data

**Dates:** 2026-10-08 – 2026-10-21
**Roadmap goal:** Catalog data + deploy: database, watch model, admin inventory management, first
deploy.
**Sprint goal:** Watches live in a database instead of in code, with a status that keeps sold
pieces off the storefront. Admin and deploy move to Sprint 5.

Planning happened late, on 2026-10-17, day 10 of 14. Until then the four stories carried over
from Sprint 3 were still in that sprint on the board, without estimates. The start-of-sprint
screenshot therefore shows the board at this late planning, not on day one.

## Stories

| Story | Issue | Points | Status |
| --- | --- | --- | --- |
| Watch data model | [#21] | 5 | Committed |
| Mark watch status | [#22] | 2 | Committed |
| Admin inventory management | [#23] | – | Moved to the backlog; a candidate for Sprint 5 |
| Deploy to production | [#24] | – | Moved to the backlog; a candidate for Sprint 5 |

**Committed: 7 points.**

Also on the branch: five more unit tests for the price filter ([#20]), drawn from equivalence
partitioning and boundary value analysis.

## Decisions made this sprint

- **Only the data stories fit.** With four days left, the sprint took the two stories that need
  no outside decision. Deploy needs a host and a Postgres provider chosen and an account created.
  Admin needs the SQLAdmin-or-hand-built decision and depends on the data model anyway.
- **Synchronous SQLAlchemy, with plain `def` routes.** Async SQLAlchemy needs async drivers and
  changes how related rows load. At this site's traffic a thread pool is plenty, so a route that
  queries the database is a plain `def`, which FastAPI runs on its thread pool.
- **Fixed lists live in the database as names, checked by the database.** Condition, box and
  papers, and status are Python enums. Each is stored as the member's name (`VERY_GOOD`) in a
  string column with a CHECK constraint, and the page prints its label ("Very Good"). A native
  Postgres enum type was ruled out because it's awkward to change in a migration.
- **Photos get their own table**, ordered by position, so the detail page's gallery ([#27]) needs
  no schema change. Alt text moved from the watch to the photo it describes.
- **A `featured` flag picks the landing page's watches**: newest listing first, at most three,
  which is the grid's width on a laptop.
- **Slugs describe the watch** (`aurelian-meridian-chronograph`), because they'll be the detail
  page's URLs.
- **Placeholder watches load by a command, not a migration.** `python -m app.cli seed` can run
  any number of times. Migrations carry only the schema, so production never receives the
  invented watches.
- **Each test gets its own in-memory SQLite database**, a fake in test-double terms. One more
  test runs the real migrations and fails if they drift from the models.
- **The owner sets a status with a command until the admin area exists**:
  `python -m app.cli status <slug> on-hold` (or `available`, or `sold`). The command calls
  `set_status()` in the inventory service, which the admin area ([#23]) will reuse, so the rule
  stays in one place.
- **A sold watch leaves the landing page on its own**, even while it's still marked featured, so
  marking it sold is the only step to remember. **A watch on hold stays, labelled "On hold"**,
  because holds fall through and a buyer may want to be next in line.

## Sprint review and retrospective

Kept out of the repository, in `docs/sprints/local/` (gitignored), because they are the owner's
written reflection and feed coursework submissions rather than the codebase.

[#20]: https://github.com/zarekcodes/makarios-luxury/issues/20
[#21]: https://github.com/zarekcodes/makarios-luxury/issues/21
[#22]: https://github.com/zarekcodes/makarios-luxury/issues/22
[#23]: https://github.com/zarekcodes/makarios-luxury/issues/23
[#24]: https://github.com/zarekcodes/makarios-luxury/issues/24
[#27]: https://github.com/zarekcodes/makarios-luxury/issues/27
