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

## Sprint review and retrospective

Kept out of the repository, in `docs/sprints/local/` (gitignored), because they are the owner's
written reflection and feed coursework submissions rather than the codebase.

[#20]: https://github.com/zarekcodes/makarios-luxury/issues/20
[#21]: https://github.com/zarekcodes/makarios-luxury/issues/21
[#22]: https://github.com/zarekcodes/makarios-luxury/issues/22
[#23]: https://github.com/zarekcodes/makarios-luxury/issues/23
[#24]: https://github.com/zarekcodes/makarios-luxury/issues/24
