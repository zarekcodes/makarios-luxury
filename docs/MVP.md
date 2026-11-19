# MVP Definition

## Product vision

Makarios Luxury sells authenticated pre-owned luxury watches. The website is the storefront:
buyers browse current inventory, see detailed photos and specs, and send an inquiry or offer on
a piece. The owner manages inventory and responds to inquiries from one admin area.

The site must feel **fast and premium on any device**, especially phones.

## Users

| User | Needs |
| --- | --- |
| **Buyer** | Browse available watches, filter by brand/price, see condition and provenance details, contact the seller about a specific piece. |
| **Owner (admin)** | Add/edit/remove listings with photos, mark pieces as on hold or sold, see and track incoming inquiries. |

## MVP scope (must have)

1. **Landing page:** brand introduction, featured watches, trust signals (authentication,
   condition grading), call to action to browse the catalog.
2. **Catalog:** grid of available watches, filterable by brand, price range, and availability.
3. **Watch detail page:** photo gallery, brand, model, reference number, year, condition,
   box/papers, price (or "price on request"), and availability status.
4. **Inquiry form:** buyer submits name, email, optional phone, message, and optional offer amount
   for a specific watch. Owner gets an email notification.
5. **Admin area:** password-protected inventory management (CRUD, photo upload, status changes)
   and a list of inquiries.
6. **Mobile-first and fast:** usable at phone width; Lighthouse performance score ≥ 90 on mobile.

## Out of scope for the MVP (candidate stretch goals)

- Online checkout / payments (Stripe)
- Buyer accounts, saved watches, wishlists
- "Sell or trade your watch" submission form
- Blog / educational content
- Admin roles and permissions (the two owners each have an account, with the same access)

## MVP is done when

A buyer on a phone can land on the site, find a watch, view its details and photos, and send an
inquiry, and the owner receives it and can manage it in the admin area, all on the deployed
production site.

## Status at the end of the semester (2026-11-19)

The scope and the definition of done above are what was agreed in Sprint 1, kept as written. This
is how the build compares, after six sprints.

| MVP scope item | Status |
| --- | --- |
| 1. Landing page | **Done.** Brand introduction, featured watches from the database, the trust section, a call to action to the catalog. |
| 2. Catalog | **Listing done** (`/watches`, every watch in stock, newest first). **Filters not built**: the price filter exists in the service layer and is tested, with no page using it (#26). |
| 3. Watch detail page | **Started, not shipped.** Name, status, price and specs, behind a feature flag that's off in production. No photo gallery (#27). |
| 4. Inquiry form | **Not built** (#31, #32). Buyers inquire by email instead: each card's Inquire link opens a message with the watch's name and reference in the subject, and the contact band offers email and an Instagram message. |
| 5. Admin area | **Inventory done**: per-owner accounts, adding and editing watches, status changes, photo upload, reordering and deleting. Deleting a watch isn't built (#69). **Inquiries list not built** (#33). |
| 6. Mobile-first and fast | **Done.** The landing page and `/watches` score 100 for mobile performance on the live site (2026-11-18), against a target of 90. |

**Against the definition of done:** a buyer on a phone can land on the live site, find a watch and
send an inquiry by email, which the owner receives. Viewing a watch on its own page, and managing
inquiries in the admin area, aren't built.

Requirement changes along the way: two owners each get an account instead of one shared
password (Sprint 5, once the business partner joined); owners' photos are stored on a Railway
volume, decided in Sprint 6. Both are recorded in the sprint notes.

