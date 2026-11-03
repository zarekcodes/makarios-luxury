# Sprint 5: Live site

**Dates:** 2026-10-22 – 2026-11-04
**Roadmap goal:** Deploy + admin: first deploy, admin inventory management.
**Sprint goal:** The site is live on a real HTTPS URL, backed by Postgres, with no placeholder
watches in production, and the owner can log in to a protected admin area.

## Stories

| Story | Issue | Points | Status |
| --- | --- | --- | --- |
| Deploy to production | [#24] | 5 | Live and checked on 2026-11-03; done when the sprint's PR merges |
| Admin login | [#54], split from [#23] | 3 | Live on 2026-11-03; done when the sprint's PR merges |

**Committed: 8 points**, against a Sprint 4 velocity of 9 points. Deploy comes first. See
"Decisions" for the checkpoint.

### Deploy to production ([#24])

As the owner, I want the site live on a real URL so that customers can use it.

Acceptance criteria:

- The site is served over HTTPS at a public Railway URL.
- Production reads Postgres through `MAKARIOS_DATABASE_URL`, and migrations run on every deploy
  before the new version takes traffic.
- Production has no placeholder watches. The landing page reads well with no watches at all.
- Debug is off in production, and no secret is in the repository.
- Lighthouse mobile performance is 90 or above on the live URL.
- The full test suite passes against a local Postgres.
- The deploy steps are documented.

Tasks:

| Task | Issue |
| --- | --- |
| Postgres driver, with migrations and tests run against Postgres | [#55] |
| Accept the host's Postgres URL (`postgresql://` to `postgresql+psycopg://`) | [#56] |
| Landing page state for when no watches are listed | [#57] |
| Production settings and pre-deploy migrations | [#58] |
| First deploy, checked live | [#59] |
| Document the deploy steps | [#60] |

### Admin login ([#54], split from [#23])

As one of the business's two owners, I want my own password-protected admin account so that only
we can change inventory, and each change can be traced to one of us.

Acceptance criteria:

- SQLAdmin is mounted at `/admin`, with a list and edit view for watches.
- Every `/admin` page redirects to a login form until an owner signs in.
- Each owner has their own account, created from the command line. Passwords are stored only as
  Argon2 hashes, in the database, never in the repository or in plain text.
- The session cookie is signed, HttpOnly, SameSite, and Secure in production.
- Repeated failed logins are slowed or refused.
- Tests cover a rejected anonymous request, a wrong password, and a successful login.

Photo upload is not part of this story. It needs the production image storage decision. Neither
are two-factor login and login alerts, which became their own story, [#65] (see "Decisions").

Tasks:

| Task | Issue |
| --- | --- |
| Mount SQLAdmin with a watch view | [#61] |
| Admin authentication backend | [#62] |
| Throttle failed admin logins | [#63] |
| Tests for admin access | [#64] |

## Backlog refinement (no points)

Before the sprint review, every remaining MVP story gets acceptance criteria and an estimate, so
Sprints 6–8 can be checked against velocity instead of guessed. [#23]'s remaining work splits
into stories that each fit a sprint: add and edit watches, photo upload, status changes from the
admin (reusing `set_status()`), and removing watches. Two-factor login and login alerts ([#65])
get their estimate too.

Done on 2026-11-03. Every open story has acceptance criteria and points on the board:

| Story | Points |
| --- | --- |
| Add watches from the admin ([#67], split from [#23]) | 2 |
| Optimized images ([#28]) | 3 |
| Photo upload ([#68], split from [#23]) | 3 |
| Remove watches from the admin ([#69], split from [#23]) | 1 |
| Catalog listing ([#25]) | 3 |
| Catalog filters ([#26]) | 3 |
| Watch detail page ([#27]) | 5 |
| Inquiry form ([#31]) | 5 |
| Inquiry notification ([#32]) | 3 |
| Inquiries in admin ([#33]) | 2 |
| SEO metadata ([#35]) | 2 |
| Performance budget ([#36]) | 3 |
| Accessibility pass ([#37]) | 2 |
| About page ([#38]) | 1 |
| Two-factor admin login and login alerts ([#65]) | 5 |
| Railway's deploy settings in the repository ([#66]) | 2 |

[#23] closed as split. Editing a watch and changing its status needed no story of their own: the
edit view built for [#54] already does both. The re-planned Sprints 6–8, the new cut line and the
open question about two-factor login are in `docs/BACKLOG.md`.

## Decisions made this sprint

- **Railway, on the Hobby plan.** $5 a month, which includes $5 of usage. The app and Postgres
  together are estimated at $5–6 a month at this site's traffic. Render's free tier was ruled out
  because its web service sleeps after 15 idle minutes and takes about a minute to wake, which
  defeats the performance goal, and its free Postgres is deleted after 30 days. Fly.io and a
  self-managed server cost more setup time than this sprint has. Railway's free trial credit
  covers the first deploy, with the move to Hobby before it runs out.
- **SQLAdmin for the admin's inventory screens, with a hand-written login.** SQLAdmin builds the
  list and edit pages from the models. The authentication backend is the part written here,
  because it's small and it's where a security mistake would come from.
- **An empty state first, real watches if they're ready.** The landing page gets a deliberate
  state for when nothing is listed, since production starts with no watches. If photos and specs
  for a few real watches are ready in time, they're entered through the admin, and their photos
  are cropped to the cards' 4:5 portrait shape and exported as WebP at 400, 800 and 1200 px.
  Their photos ship as static files until photo upload has storage.
- **Deploy before login, with a checkpoint on 2026-11-01.** If deploy isn't done by then, admin
  login isn't started. It stays in the sprint, unfinished, for the end-of-sprint screenshot.
- **Railway's signups are paused, so the deploy waits until 2026-10-30, with Render as the
  fallback.** Railway paused new signups on 2026-10-22, after a security incident on 2026-10-21,
  and on 2026-10-28 it still gave no date for reopening them
  ([status](https://status.railway.com/incident/O1VGXWU5)). The code for the deploy is finished
  and passes CI on SQLite and Postgres, so only the account is missing. If signups are still
  paused at the end of 2026-10-30, production moves to Render: an always-on Starter web service
  and its smallest Postgres, about $13 a month against Railway's $5–6. The same Dockerfile
  carries over, and Render also runs migrations in a pre-deploy step and only swaps to a new
  version once it starts cleanly.
- **Production moved to Render on 2026-11-01.** Railway's signups were still paused after the
  cutoff, and its last update, on 2026-10-29, gave no date. Render costs about $13 a month, against
  Railway's estimated $5–6: an always-on web service at $7 and the smallest Postgres at about
  $6–7. Only the host's configuration changed, from `railway.toml` to `render.yaml`. The
  database now accepts no connections from the internet, and Render generates the secret key.
  Render compresses responses at its proxy, so the app's gzip middleware came out.
- **Back to Railway on 2026-11-03, before anything was deployed.** Railway reopened signups on
  2026-11-02 ([status](https://status.railway.com/incident/O1VGXWU5)), with a paid plan required
  before the first deploy. With the reason for leaving gone, its lower cost decided it: about
  $5–6 a month against Render's $13, roughly $12 less over the rest of the semester. The risk
  accepted is a host 12 days past an incident in which some customers' stored secrets were
  decrypted. The two secrets stored there, the session key and the database URL, can each be
  rotated in minutes, and there's no customer data yet. `railway.toml` came back, and so did the
  app's gzip middleware, since Railway doesn't document compressing responses. Railway's staff say
  its edge replaces `X-Forwarded-For` rather than adding to it, so the throttle's default of one
  proxy hop fits, which the live check confirms.
- **Login was built while the deploy waited.** The checkpoint existed to keep effort on the
  deploy, and from 2026-10-28 the deploy needed only an account. So both stories were finished
  before the checkpoint, and the first deploy carries both.
- **The login throttle could be bypassed, and was fixed before any deploy.** It read the client
  address from the first entry of `X-Forwarded-For`, which a visitor can make up, so changing it
  on each attempt avoided the limit. It now counts from the end of the header. A test that sent
  repeated failures from one fixed client had passed, and the bug was found by checking how the
  header behaves behind a proxy while choosing the new host. The tests now cover a made-up entry.
- **Railway's deploy settings live in its dashboard, for now.** The first live deploy served 500s:
  Railway had never read `railway.toml`, so the migrations never ran and no health check gated
  traffic. Railway's docs say new services can't use that file at all, and it stops working for
  older ones on 2026-12-01. The pre-deploy command and health check path were set in the
  service's settings instead, `railway.toml` was removed, and `docs/DEPLOY.md` lists both
  settings. Railway's replacement, Infrastructure as Code, is a TypeScript file by default (Python
  is in beta), so moving the settings back into the repository is a backlog item rather than a
  same-day change.
- **Live check, 2026-11-03.** https://makarios-luxury-production.up.railway.app serves over HTTPS
  with both migrations applied on Postgres and no placeholder watches. PageSpeed Insights on
  mobile scored 100 for performance, accessibility, best practices and SEO (first contentful
  paint 0.8 s, largest contentful paint 1.2 s, total blocking time 0 ms, layout shift 0), against
  a target of 90. The API docs are hidden, `/admin` redirects to its login, and pages are gzipped.
- **Owner accounts wait for Sprint 6.** The login is live and tested, but no account exists in
  production yet. The owner creates one at the start of Sprint 6 (`docs/DEPLOY.md`), and the
  business partner's account waits until after the semester. The sprint review shows the login
  page and a refused password, rather than a signed-in admin.
- **The throttle counts two proxies on Railway.** The live check showed Railway's edge replaces a
  visitor's `X-Forwarded-For` with their real address, and that a Railway proxy then appends its
  own. With one hop, the throttle would have counted by the proxy's address, so every visitor would
  share one count. `MAKARIOS_PROXY_HOPS` is set to 2 in production, and a forged two-entry header
  was confirmed to be dropped by the edge.
- **Two owners, each with an account; two-factor login is its own story.** On 2026-10-28, before
  login work started, it became clear the owner's business partner, who is less technical, will
  use the admin too. [#54] now gives each owner an account in an `admin_users` table instead of
  one shared password hash in an environment variable, so either account can be revoked alone and
  the table has a place for a second factor. Its estimate stays at 3 points. Two-factor login
  went to a new story, [#65], aimed at Sprint 6, rather than into this sprint, which is already
  waiting on Railway. Authenticator-app codes (TOTP) were chosen as the second factor: free, with
  no outside service, and enforced by the app. Sign in with Google would rest on each person's
  Google account settings, which the app can't check. SMS costs money monthly, needs US carrier
  registration before the first message, and is open to SIM swapping. A Discord webhook works as
  a login alert, not as a factor, since a shared channel would let either owner approve the
  other's login.
- **Image storage in production moves to Sprint 6**, with photo upload.

[#23]: https://github.com/zarekcodes/makarios-luxury/issues/23
[#24]: https://github.com/zarekcodes/makarios-luxury/issues/24
[#54]: https://github.com/zarekcodes/makarios-luxury/issues/54
[#55]: https://github.com/zarekcodes/makarios-luxury/issues/55
[#56]: https://github.com/zarekcodes/makarios-luxury/issues/56
[#57]: https://github.com/zarekcodes/makarios-luxury/issues/57
[#58]: https://github.com/zarekcodes/makarios-luxury/issues/58
[#59]: https://github.com/zarekcodes/makarios-luxury/issues/59
[#60]: https://github.com/zarekcodes/makarios-luxury/issues/60
[#61]: https://github.com/zarekcodes/makarios-luxury/issues/61
[#62]: https://github.com/zarekcodes/makarios-luxury/issues/62
[#63]: https://github.com/zarekcodes/makarios-luxury/issues/63
[#64]: https://github.com/zarekcodes/makarios-luxury/issues/64
[#65]: https://github.com/zarekcodes/makarios-luxury/issues/65
[#25]: https://github.com/zarekcodes/makarios-luxury/issues/25
[#26]: https://github.com/zarekcodes/makarios-luxury/issues/26
[#27]: https://github.com/zarekcodes/makarios-luxury/issues/27
[#28]: https://github.com/zarekcodes/makarios-luxury/issues/28
[#31]: https://github.com/zarekcodes/makarios-luxury/issues/31
[#32]: https://github.com/zarekcodes/makarios-luxury/issues/32
[#33]: https://github.com/zarekcodes/makarios-luxury/issues/33
[#35]: https://github.com/zarekcodes/makarios-luxury/issues/35
[#36]: https://github.com/zarekcodes/makarios-luxury/issues/36
[#37]: https://github.com/zarekcodes/makarios-luxury/issues/37
[#38]: https://github.com/zarekcodes/makarios-luxury/issues/38
[#66]: https://github.com/zarekcodes/makarios-luxury/issues/66
[#67]: https://github.com/zarekcodes/makarios-luxury/issues/67
[#68]: https://github.com/zarekcodes/makarios-luxury/issues/68
[#69]: https://github.com/zarekcodes/makarios-luxury/issues/69
