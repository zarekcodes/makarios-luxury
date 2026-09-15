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
- Multiple admin users and roles

## MVP is done when

A buyer on a phone can land on the site, find a watch, view its details and photos, and send an
inquiry, and the owner receives it and can manage it in the admin area, all on the deployed
production site.
