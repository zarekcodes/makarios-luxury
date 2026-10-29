# Sprint 5: Live site

**Dates:** 2026-10-22 – 2026-11-04
**Roadmap goal:** Deploy + admin: first deploy, admin inventory management.
**Sprint goal:** The site is live on a real HTTPS URL, backed by Postgres, with no placeholder
watches in production, and the owner can log in to a protected admin area.

## Stories

| Story | Issue | Points | Status |
| --- | --- | --- | --- |
| Deploy to production | [#24] | 5 | In progress: built and passing CI; the live deploy waits on a Railway account |
| Admin login | [#54], split from [#23] | 3 | In progress: built; ships once the deploy is live |

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
| Accept Railway's Postgres URL (`postgresql://` to `postgresql+psycopg://`) | [#56] |
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
- **Image storage in production moves to Sprint 6**, with photo upload. Railway offers volumes and
  object storage, so the choice stays on one platform.

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
