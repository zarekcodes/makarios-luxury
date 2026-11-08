# Sprint 6: Real inventory

**Dates:** 2026-11-05 – 2026-11-18
**Roadmap goal:** Real inventory: add watches, image pipeline, photo upload.
**Sprint goal:** The owners can list a real watch from the admin, with fast-loading photos stored
somewhere that survives a deploy.

## Stories

| Story | Issue | Points | Status |
| --- | --- | --- | --- |
| Add watches from the admin | [#67], split from [#23] | 2 | Todo |
| Optimized images | [#28] | 3 | Todo |
| Photo upload | [#68], split from [#23] | 3 | Todo |

**Committed: 8 points**, against a velocity of about 8.5 (9 in Sprint 4, 8 in Sprint 5). Add
watches comes first, since it's the smallest and the other two attach photos to the watches it
creates. Photo upload depends on the image pipeline, so it goes last.

### Add watches from the admin ([#67])

As an owner, I want to add a watch from the admin so that a new piece can be listed without
touching code.

Acceptance criteria:

- `/admin` has an **Add** action for watches, with every catalog field. A blank price means price
  on request.
- The slug comes from the brand and model through `slugify` and `unique_slug` ([#52]), never typed.
- Required fields, a sensible year and a positive whole-dollar price are validated beside the field.
- A featured watch appears on the landing page right after it's saved.
- The audit log records who added it.

### Optimized images ([#28])

As a buyer on a phone, I want images that load fast so that browsing feels smooth.

Acceptance criteria:

- A pipeline in `app/services/` turns one photo into 4:5 WebP files at 400, 800 and 1200 px, with
  metadata (GPS included) stripped.
- Non-images and oversized files are refused with a clear error.
- Each 1200 px file stays under a set budget (about 250 KB).
- Output names match what `responsive_img` already serves, so templates don't change.

### Photo upload ([#68])

As an owner, I want to add, order and remove a watch's photos from the admin so that every listing
shows the real piece.

Acceptance criteria:

- The admin edit page accepts uploads, which go through the image pipeline ([#28]).
- Files live in storage that survives a deploy (a Railway bucket or volume, decided in this story).
- Alt text is required before a photo saves.
- Owners can reorder and delete photos, and the first photo is what cards show.
- Works from a phone.

## Decisions

- **Two-factor login ([#65]) stays below the cut line.** Agreed for Sprint 6 on 2026-10-28, but
  taking it would push every MVP story back a sprint and the inquiry stories out of the semester.
  The admin holds no personal data until inquiries arrive, and per-owner passwords plus the login
  throttle protect it until then.

[#23]: https://github.com/zarekcodes/makarios-luxury/issues/23
[#28]: https://github.com/zarekcodes/makarios-luxury/issues/28
[#52]: https://github.com/zarekcodes/makarios-luxury/issues/52
[#65]: https://github.com/zarekcodes/makarios-luxury/issues/65
[#67]: https://github.com/zarekcodes/makarios-luxury/issues/67
[#68]: https://github.com/zarekcodes/makarios-luxury/issues/68
