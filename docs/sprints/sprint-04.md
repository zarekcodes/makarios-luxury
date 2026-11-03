# Sprint 4: Catalog data

**Dates:** 2026-10-08 – 2026-10-21
**Roadmap goal:** Catalog data + deploy: database, watch model, admin inventory management, first
deploy.
**Sprint goal:** Watches live in a database instead of in code, with a status that keeps sold
pieces off the storefront. Admin and deploy move to Sprint 5.

## Stories

| Story | Issue | Points | Status |
| --- | --- | --- | --- |
| Watch data model | [#21] | 5 | Done |
| Mark watch status | [#22] | 2 | Done |
| Price filter tests: lower bound, open range, invalid range | [#50], a task of [#26] | 1 | Done on 2026-10-11 |
| Generate watch slugs test-first | [#52], a task of [#23] | 1 | Done on 2026-10-18, added during the sprint; reviewed in [#51] |
| Admin inventory management | [#23] | – | Moved to the backlog; a candidate for Sprint 5 |
| Deploy to production | [#24] | – | Moved to the backlog; a candidate for Sprint 5 |

**Committed: 7 points at planning. Completed: 9 points**, adding 1 for the price filter tests
and 1 for the slug work added during the sprint. The tests grew from 40 to
79. Each story is one commit on the `sprint-4` branch; the slug work arrives as its own merged
pull request, one commit per red, green and refactor step.

[#50] adds five unit tests to the price filter from [#20], drawn from equivalence partitioning
and boundary value analysis. Its story, [#26], isn't in this sprint, so like [#20] in Sprint 3 the
task carries its own point.

[#52] was done test-first for a course assignment (five red-green-refactor cycles) and reviewed
in its own pull request, [#51], before merging into `sprint-4`. Its story, admin inventory
management ([#23]), is in the backlog, so it also carries its own point. It gives the admin area
the slugs it will need when the owner adds a watch.

## Tasks

Each story is split into tasks on the board, as its sub-issues. The tasks were split out on
2026-10-17, after the code was written, so their created dates come after the commits. They show
each story's technical slices, not a plan made in advance. The points stay on the stories, so the
Velocity view counts each point once.

| Task | Issue | Story |
| --- | --- | --- |
| Watch and Photo models with checked enums | [#42] | [#21] |
| Database engine and per-request session | [#43] | [#21] |
| Alembic setup, first migration, and drift test | [#44] | [#21] |
| Seed command for the placeholder watches | [#45] | [#21] |
| Landing page reads featured watches from the database | [#46] | [#21] |
| In-memory test database and model tests | [#47] | [#21] |
| Inventory service and status command | [#48] | [#22] |
| Hide sold watches, label watches on hold | [#49] | [#22] |

The story commits close [#21] and [#22]. The tasks close through the sprint pull request's
description, which lists each one.

## Decisions made this sprint

- **Only the data stories fit.** The sprint took the two stories that need no outside
  decision. Deploy needs a host and a Postgres provider chosen and an account created.
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
[#26]: https://github.com/zarekcodes/makarios-luxury/issues/26
[#42]: https://github.com/zarekcodes/makarios-luxury/issues/42
[#43]: https://github.com/zarekcodes/makarios-luxury/issues/43
[#44]: https://github.com/zarekcodes/makarios-luxury/issues/44
[#45]: https://github.com/zarekcodes/makarios-luxury/issues/45
[#46]: https://github.com/zarekcodes/makarios-luxury/issues/46
[#47]: https://github.com/zarekcodes/makarios-luxury/issues/47
[#48]: https://github.com/zarekcodes/makarios-luxury/issues/48
[#49]: https://github.com/zarekcodes/makarios-luxury/issues/49
[#50]: https://github.com/zarekcodes/makarios-luxury/issues/50
[#51]: https://github.com/zarekcodes/makarios-luxury/pull/51
[#52]: https://github.com/zarekcodes/makarios-luxury/issues/52
