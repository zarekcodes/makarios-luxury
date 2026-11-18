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
| 4 | **Catalog data:** database, watch model, watch status (admin + deploy moved to Sprint 5) |
| 5 | **Live site:** first deploy (Railway), admin login (catalog pages moved to Sprint 6) |
| 6 | **Real inventory:** add watches, image pipeline, photo upload (8 points; catalog listing pulled in once they're done) |
| 7 | **Browse + inquire** (proposed): watch detail page, inquiry form (10 points) |
| 8 | **Final demo** (proposed, one week, ends 2026-12-09): inquiry notification (3 points; inquiries in admin as a stretch) |

Deploying early rather than at the end means every sprint after that ships a working increment
to a live URL. That's a core Agile principle and makes sprint reviews real demos.

Sprint 3 went to the landing page refresh, so its data and deploy work moved to Sprint 4. Sprint 4
took only the data stories, so admin and deploy moved again, to Sprint 5, which delivered both.

### Sprints 6–8, re-planned at Sprint 5's backlog refinement

Every remaining story now has acceptance criteria and an estimate on the board: 45 points in
all. Velocity is about 8.5 points a sprint (9 in Sprint 4, 8 in Sprint 5), so the three sprints
left hold about 25. The plan follows the MVP's definition of done, in order: owners can list a
real watch with photos, buyers can browse and open it, and buyers can send an inquiry the owners
receive and track.

| Sprint | Stories | Points |
| --- | --- | --- |
| 6 | Add watches (#67), optimized images (#28), photo upload (#68) | 8 |
| 7 | Catalog listing (#25), watch detail page (#27) | 8 |
| 8 | Inquiry form (#31), inquiry notification (#32), inquiries in admin (#33) | 10 |

Sprint 8 is 1.5 points over velocity. If it slips, inquiries in admin (#33) goes first: the owners
still get every inquiry by email.

**Below the semester's cut line**, in rough order of value: two-factor admin login (#65, 5),
catalog filters (#26, 3; with the business's inventory size a single page is easy to scan),
performance budget (#36, 3; each page story already requires a mobile score of 90 or above),
removing watches (#69, 1), accessibility pass (#37, 2), SEO metadata (#35, 2), the About page
(#38, 1; it also needs the owners' text), and Railway's settings in code (#66, 2). Testimonials,
shop by brand, the sold archive, the sell-or-source form and the blog stay out.

**Decided at Sprint 6 planning:** two-factor login (#65) stays below the cut line (see
`sprints/sprint-06.md`). Until inquiries arrive the admin holds no personal data, and per-owner
passwords and the login throttle protect it.

### Sprints 6–8, re-planned on 2026-11-10 for the final presentation

The final presentations are on 2026-12-09, a Wednesday. Two-week sprints would end Sprint 8 on
2026-12-16, a week too late, so Sprint 8 is cut to one week (2026-12-03 to 2026-12-09) and the
work moves earlier:

| Sprint | Dates | Stories | Points |
| --- | --- | --- | --- |
| 6 | 11-05 – 11-18 | Add watches (#67), optimized images (#28), photo upload (#68); then catalog listing (#25) | 8, +3 |
| 7 | 11-19 – 12-02 | Watch detail page (#27), inquiry form (#31) | 10 |
| 8 | 12-03 – 12-09 | Inquiry notification (#32); inquiries in admin (#33) only if there's time | 3 (+2) |

Catalog listing (#25) is already started behind its flag, and is pulled into Sprint 6 at
refinement once the three committed stories are done, which keeps Sprint 7 near velocity. Sprint 8
leaves room to rehearse the demo against a site that has stopped changing. The MVP's definition
of done still holds without #33: the owners get every inquiry by email.

## Epics

Each epic is an issue, and its stories are its sub-issues on the board.

- **Foundations** ([#1]), Sprint 1: the repository, scaffolding, CI, the MVP and architecture docs,
  and the backlog. The board itself was added on the last day of Sprint 3.
- **Landing page** ([#2]), Sprints 2–3: a responsive landing page on placeholder content, then a
  photo-led refresh with one obvious way to ask about a watch.
- **Catalog** ([#3]), Sprints 4–7: watches in a database, the first deploy and admin login, then
  adding watches with photos (Sprint 6) and the catalog listing and detail page (Sprint 7).
  Filters are below the semester's cut line. Stretch: shop by
  brand, and an archive of watches already sold.
- **Inquiries** ([#4]), Sprint 8: an inquiry or offer form for a specific watch, an email to the
  owner, and inquiries tracked in the admin area. Stretch: a form for selling a watch to Makarios
  or asking it to source one.
- **Polish** ([#5]), below the semester's cut line: SEO metadata, a mobile performance budget, an
  accessibility pass and an About page. Each page story carries its own performance target. Stretch: testimonials, real and attributed only.
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
