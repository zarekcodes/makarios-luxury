# Product Backlog (seed)

Initial backlog for creating GitHub Issues. Once the issues exist, **GitHub Projects is the source
of truth**. This file is only the starting snapshot. Estimate points during sprint planning.

## Roadmap (tentative, re-planned every sprint)

| Sprint | Goal |
| --- | --- |
| 1 | **Foundations:** repo, scaffolding, CI, MVP + architecture defined, backlog created |
| 2 | **Landing page MVP:** responsive, polished landing page using static placeholder content |
| 3 | **Catalog data + deploy:** database, watch model, admin inventory management, first deploy |
| 4 | **Catalog pages:** listing with HTMX filters, detail page with gallery, image pipeline |
| 5 | **Inquiries:** inquiry/offer form, email notification, inquiries in admin |
| 6 | **Polish:** SEO, performance (Lighthouse ≥ 90), accessibility, About/Contact pages |
| 7 | **Hardening + final demo:** bug fixes, stretch goals if time allows |

Deploying in Sprint 3 rather than at the end means every sprint after that ships a working
increment to a live URL. That's a core Agile principle and makes sprint reviews real demos.

## Epics and user stories

### Epic: Foundations (`epic:foundations`), Sprint 1
- **Project scaffolding.** As the developer, I want a runnable app skeleton with tests and CI so
  that every future change is verified automatically.
- **MVP and architecture docs.** As the developer, I want the MVP scope and architecture written
  down so that sprint planning has a clear target.
- **Backlog and board setup.** As the developer, I want the backlog in GitHub Projects so that
  sprint progress is visible and traceable.

### Epic: Landing page (`epic:landing`), Sprint 2
- **Frontend tooling.** As the developer, I want Tailwind and htmx wired into the base template
  so that pages can be styled and made interactive.
- **Site header and navigation.** As a buyer, I want clear navigation that collapses into a menu
  on mobile so that I can get around on any device.
- **Hero section.** As a buyer, I want a striking first impression that tells me what Makarios
  sells so that I trust the site and keep browsing.
- **Featured watches.** As a buyer, I want to see a few highlighted watches on the landing page
  so that I'm drawn into the catalog.
- **Trust section.** As a buyer, I want to see how watches are authenticated and graded so that
  I feel confident buying a high-value piece.
- **Footer.** As a buyer, I want contact info and social links in the footer so that I can reach
  the business.

### Epic: Catalog (`epic:catalog`), Sprints 3–4
- **Watch data model.** As the owner, I want watches stored with brand, model, reference, year,
  condition, box/papers, price, status, and photos so that listings are complete and consistent.
- **Admin inventory management.** As the owner, I want to add, edit, and remove watches and
  upload photos so that I can keep inventory current without touching code.
- **Mark watch status.** As the owner, I want to mark a watch available, on hold, or sold so that
  buyers only pursue watches that are actually for sale.
- **Deploy to production.** As the owner, I want the site live on a real URL so that customers
  can use it.
- **Catalog listing.** As a buyer, I want to browse all available watches in a grid so that I can
  see what's in stock.
- **Catalog filters.** As a buyer, I want to filter by brand and price without a full page reload
  so that I can find what I want quickly.
- **Watch detail page.** As a buyer, I want a page with every detail and a photo gallery so that I
  can evaluate a watch before contacting the seller.
- **Optimized images.** As a buyer on a phone, I want images that load fast so that browsing
  feels smooth.

### Epic: Inquiries (`epic:inquiries`), Sprint 5
- **Inquiry form.** As a buyer, I want to send a question or offer about a specific watch so that
  I can start the buying process.
- **Inquiry notification.** As the owner, I want an email when an inquiry arrives so that I can
  respond quickly.
- **Inquiries in admin.** As the owner, I want to see and mark inquiries as handled so that none
  fall through the cracks.

### Epic: Polish (`epic:polish`), Sprint 6
- **SEO metadata.** As the owner, I want proper titles, descriptions, and social previews on every
  page so that listings show up well in search and when shared.
- **Performance budget.** As a buyer, I want every page to score ≥ 90 on mobile Lighthouse so that
  the site feels instant.
- **Accessibility pass.** As a buyer using assistive tech, I want the site to be navigable by
  keyboard and screen reader.
- **About page.** As a buyer, I want to learn about the business so that I trust who I'm buying
  from.
