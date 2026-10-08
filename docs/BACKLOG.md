# Roadmap and epics

The backlog itself is the [project board](https://github.com/users/zarekcodes/projects/2): every
story is an issue, filed as a sub-issue of its epic, with its sprint, status and points. This file
keeps what a board shows poorly: the sprint-by-sprint roadmap and a summary of each epic. See
`docs/WORKFLOW.md` for how the board is used.

## Roadmap (tentative, re-planned every sprint)

| Sprint | Goal |
| --- | --- |
| 1 | **Foundations:** repo, scaffolding, CI, MVP + architecture defined, backlog created |
| 2 | **Landing page MVP:** responsive, polished landing page using static placeholder content |
| 3 | **Landing page refresh:** photo-led redesign (catalog data + deploy carried over) |
| 4 | **Catalog data + deploy:** database, watch model, admin inventory management, first deploy |
| 5 | **Catalog pages:** listing with HTMX filters, detail page with gallery, image pipeline |
| 6 | **Inquiries:** inquiry/offer form, email notification, inquiries in admin |
| 7 | **Polish:** SEO, performance (Lighthouse ≥ 90), accessibility, About/Contact pages |
| 8 | **Hardening + final demo:** bug fixes, stretch goals if time allows |

Deploying in Sprint 4 rather than at the end means every sprint after that ships a working
increment to a live URL. That's a core Agile principle and makes sprint reviews real demos.

Sprint 3 went to the landing page refresh, so its data and deploy work, and every sprint after
it, moved back by one. Sprint 4 planning decides whether the semester has room for an eighth
sprint or later scope gets cut.

## Epics

Each epic is an issue, and its stories are its sub-issues on the board.

- **Foundations** ([#1]), Sprint 1: the repository, scaffolding, CI, the MVP and architecture docs,
  and the backlog. The board itself was added on the last day of Sprint 3.
- **Landing page** ([#2]), Sprints 2–3: a responsive landing page on placeholder content, then a
  photo-led refresh with one obvious way to ask about a watch.
- **Catalog** ([#3]), Sprints 4–5: watches in a database, admin inventory management and the first
  deploy, then the catalog listing, filters, detail page and optimized images. Stretch: shop by
  brand, and an archive of watches already sold.
- **Inquiries** ([#4]), Sprint 6: an inquiry or offer form for a specific watch, an email to the
  owner, and inquiries tracked in the admin area. Stretch: a form for selling a watch to Makarios
  or asking it to source one.
- **Polish** ([#5]), Sprint 7: SEO metadata, a mobile performance budget, an accessibility pass and
  an About page. Stretch: testimonials, real and attributed only.
- **Blog** ([#6]), stretch, Sprint 8 or after the MVP: posts in the owner's own voice, answering the
  questions prospective buyers ask most. `MVP.md` lists it as a stretch goal. Its stories are rough
  and get split into issues when the epic is scheduled.
- **Internal dashboard** ([#7]), after the MVP: a private dashboard for the owner and partner on the
  shared backend. See "Future: internal dashboard" in `ARCHITECTURE.md`.

[#1]: https://github.com/zarekcodes/makarios-luxury/issues/1
[#2]: https://github.com/zarekcodes/makarios-luxury/issues/2
[#3]: https://github.com/zarekcodes/makarios-luxury/issues/3
[#4]: https://github.com/zarekcodes/makarios-luxury/issues/4
[#5]: https://github.com/zarekcodes/makarios-luxury/issues/5
[#6]: https://github.com/zarekcodes/makarios-luxury/issues/6
[#7]: https://github.com/zarekcodes/makarios-luxury/issues/7
