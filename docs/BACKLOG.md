# Product Backlog (seed)

**This file is the backlog.** Stories are pulled from here into `docs/sprints/sprint-NN.md` at
sprint planning and estimated there. See `docs/WORKFLOW.md` for why tracking lives in the repo
rather than in GitHub Issues.

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
- **Landing page refresh** (Sprint 3). As a buyer, I want the landing page to lead with striking
  watch photography, say plainly what Makarios sells, and give me one obvious way to ask about a
  watch, so that I'm drawn in and know what to do next. *Acceptance:* a full-bleed photo hero that
  works at 400px and on desktop, text contrast measured over the photo, an inquiry link on every
  watch card, a closing contact band, and mobile Lighthouse performance still ≥ 90.

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
- **Shop by brand** (stretch). As a buyer, I want to jump straight to the brands I collect so that I
  don't scroll past everything else.
- **Previously sold archive** (stretch). As a buyer, I want to see watches Makarios has already sold
  so that I can judge the dealer's track record and the kind of pieces they handle.

### Epic: Inquiries (`epic:inquiries`), Sprint 5
- **Inquiry form.** As a buyer, I want to send a question or offer about a specific watch so that
  I can start the buying process.
- **Inquiry notification.** As the owner, I want an email when an inquiry arrives so that I can
  respond quickly.
- **Inquiries in admin.** As the owner, I want to see and mark inquiries as handled so that none
  fall through the cracks.
- **Sell or source a watch** (stretch). As someone selling a watch, or looking for a specific
  reference, I want a form for exactly that so that I can reach Makarios without writing the email
  from scratch. Makarios already buys watches and sources on request; today the landing page's
  contact band only mentions it.

### Epic: Polish (`epic:polish`), Sprint 6
- **SEO metadata.** As the owner, I want proper titles, descriptions, and social previews on every
  page so that listings show up well in search and when shared.
- **Performance budget.** As a buyer, I want every page to score ≥ 90 on mobile Lighthouse so that
  the site feels instant.
- **Accessibility pass.** As a buyer using assistive tech, I want the site to be navigable by
  keyboard and screen reader.
- **About page.** As a buyer, I want to learn about the business so that I trust who I'm buying
  from.
- **Testimonials** (stretch). As a buyer, I want to read what past clients say so that I trust a
  dealer I haven't bought from before. Real, attributed reviews only, never invented ones.

### Epic: Blog (`epic:blog`), stretch: Sprint 7 or after the MVP
Gives the site the owner's own voice. Posts answer the questions that come up again and again with
prospective buyers, and with anyone who finds out he resells watches. `MVP.md` already lists "Blog
/ educational content" as a stretch goal. The stories are rough and will be split and estimated when
the epic is scheduled.
- **Blog list and post pages.** As a buyer, I want to read the owner's take on common watch
  questions so that I get to know who I'd be buying from and trust his judgement before I ask
  about a piece.
- **Writing a post without touching templates.** As the owner, I want to write and publish a post
  in plain text (such as Markdown) so that sharing an answer is as easy as giving it in person.
  *To decide when scheduled:* Markdown files in the repo, rendered by the server (simplest, and the
  fastest pages), or posts in the database and edited in the admin area.
- **Latest posts on the landing page.** As a buyer, I want to see a few recent posts on the home
  page so that I find them without looking for them.
- **Linking posts to watches.** As a buyer reading a post such as "our favourite watches under
  $5,000", I want to reach the watches it mentions that are in stock so that I can act on the
  advice.

Seed topics from the owner: *What to buy a new grad* and *Our favourite watches under $X*. More in
the same vein, suggestions only: buying a first "real" watch, whether box and papers matter, and
what "unworn" actually means.

### Epic: Internal dashboard (`epic:dashboard`), after the MVP
Long-term direction; see "Future: internal dashboard" in `ARCHITECTURE.md`. Stories are rough
and will be split and estimated when the epic is scheduled.
- **Dashboard access.** As the owner, I want my partner and me to log in with separate accounts
  so that business data stays private.
- **First source ingestion.** As the owner, I want one sourcing channel scraped on a schedule so
  that new listings show up without manual searching.
- **Deal and inventory records.** As the owner, I want purchases, sales, and costs recorded so
  that profit per watch is computed automatically.
- **KPI overview.** As the partner, I want a single page of key metrics (margin, turnover time,
  inventory value) so that I can see performance at a glance.
- **Price forecasting.** As the owner, I want estimated resale prices for a reference so that I
  can judge whether a listing is a good buy.
