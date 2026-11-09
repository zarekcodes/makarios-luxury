# Deploying

Production runs on [Railway](https://railway.com) (Hobby plan): one service built from this
repository's `Dockerfile`, and one Railway Postgres database. Railway deploys on every push to the
branch the service follows, once CI passes. Why Railway, and the short detour to Render while its
signups were paused, are recorded in
[Sprint 5's decisions](sprints/sprint-05.md#decisions-made-this-sprint).

## What happens on a deploy

1. A push reaches the branch the service follows. With **Wait for CI** on, Railway waits until
   GitHub Actions (lint, tests on SQLite and on Postgres, the CSS check) has passed.
2. Railway builds the image from `Dockerfile`, which it finds on its own.
3. **Pre-deploy:** `alembic upgrade head` runs in the new image, against the production database.
   If it fails, the deploy stops there and the previous version keeps serving.
4. The new container starts (`fastapi run`, on the port Railway assigns through `$PORT`).
5. Railway calls `/api/health` until it answers 200, then moves traffic to the new version and
   stops the old one. A version that never becomes healthy never takes traffic.

Steps 3 and 5 happen only because of two settings on the service (see
[First-time setup](#first-time-setup)). They live in Railway's dashboard, not in this repository:
new Railway services can't read a `railway.toml`, which Railway has deprecated. Without them a
deploy skips the migrations and takes traffic as soon as its container starts, healthy or not.

Migrations run before the code that needs them, so a new version never runs against an old schema.
The old version keeps running for a few seconds after the migration, so a migration has to leave
the schema usable by the previous release. That rules out dropping or renaming a column in the
same release that stops using it. Do it in two deploys.

## Environment variables

Set on the app service under **Variables**. None of them live in the repository.

| Variable | Value | Why |
| --- | --- | --- |
| `MAKARIOS_ENVIRONMENT` | `production` | Turns on the production checks: no debug, no API docs, no seeding. |
| `MAKARIOS_DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | A reference to the database service's private URL. The app rewrites its `postgresql://` scheme to use psycopg 3. |
| `MAKARIOS_SECRET_KEY` | a generated key (see below) | Signs the admin's session cookie. Anyone who has it can forge a login, so it lives only here. |
| `MAKARIOS_PROXY_HOPS` | `2` on Railway (see [Checking the throttle's address](#checking-the-throttles-address)) | Which entry of `X-Forwarded-For` is the visitor's address, for the login throttle. |

Generate the secret key by running this **in a terminal**, then paste the 43 characters it
prints, not the command itself:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Set only the variables in this table. In particular, leave out `MAKARIOS_DEBUG`: it defaults to
off, and `.env.example`'s `MAKARIOS_DEBUG=true` is for development only.

Railway sets `PORT` itself. The app refuses to start in production if debug is on, if
`MAKARIOS_DATABASE_URL` is missing or isn't Postgres, or if the secret key is missing, shorter
than 32 characters, or contains spaces, quotes or brackets, which a
generated key never does. A settings error in the logs never shows the values it was given.
Changing the secret key signs every owner out, which also makes it the emergency logout.

Railway had a security incident on 2026-10-21 in which some customers' stored variables were
decrypted. If it ever announces another, rotate both secrets: generate a new secret key, and
regenerate the Postgres password from the database service's settings.

## First-time setup

1. Sign up at railway.com with GitHub, and subscribe to the **Hobby** plan ($5 a month, which
   includes $5 of usage). Since 2026-11-02 a paid plan is required before the first deploy.
2. **New Project → Deploy from GitHub repo →** `zarekcodes/makarios-luxury`. Give Railway access
   to this repository only. Railway may start a first deploy straight away. It runs without the
   variables below, so let it be replaced once they're set.
3. In the service's **Settings → Source**, set the branch (see [Which branch](#which-branch)) and
   turn on **Wait for CI**.
4. On the project canvas, click **+ New** and choose **PostgreSQL** (or press Ctrl/Cmd+K and
   search for it). Leave its name as `Postgres`, since the variable reference above uses it.
5. Set the variables above on the app service.
6. In the app service's **Settings → Deploy**:
   - **+ Add pre-deploy step:** `alembic upgrade head`
   - **Healthcheck Path:** `/api/health`

   Leave **Custom Start Command** empty; the `Dockerfile` provides it. Then deploy the staged
   changes, and check that the deploy log shows `Running upgrade`.
7. **Settings → Networking → Generate Domain** for the public `*.up.railway.app` HTTPS URL.
8. Create the owners' accounts (see [Admin accounts](#admin-accounts)), then run the checks below.

## Which branch

The service follows **`main`**, so production is whatever `main` holds. A push to a sprint branch
runs CI and deploys nothing. Work reaches `main` only through a pull request from the sprint
branch, and the **Protect main** ruleset (Settings → Rules → Rulesets) enforces that: no direct
pushes, force-pushes or deletion; every required CI check must pass before the merge; and merges
are merge commits only, so the per-story commits survive.

The required checks are listed by name: `test (Python 3.12)`, `test (Python 3.14)`,
`test-postgres` and `css`. Renaming a CI job or changing its matrix means updating the ruleset to
match. Otherwise the pull request waits forever for a check that never reports.

During Sprint 5 the service followed `sprint-5` instead, so the site could go live within the
sprint. It moved to `main` once that sprint's pull request merged.

## Checking a deploy

```bash
curl -s https://<domain>/api/health                                         # {"status":"ok"}
curl -s -o /dev/null -D - -H 'Accept-Encoding: gzip' https://<domain>/ | grep -i content-encoding
```

Then load the home page on a phone, and run PageSpeed Insights (mobile) on the URL. The target is
a performance score of 90 or above.

### Checking the throttle's address

The login throttle has to find the visitor's address in `X-Forwarded-For`. A visitor can write
anything there, and some proxies add to the end of what was sent instead of replacing it.
On 2026-11-03 the check below found that Railway's edge replaces whatever the visitor sent with
their real address, and then a Railway proxy appends its own address (`89.222.103.x`, varying):

```
forwarded=['<your IP>, 89.222.103.194']
```

So the visitor is the second entry from the end, and Railway needs `MAKARIOS_PROXY_HOPS=2`. With
the default of `1`, every visitor shares the proxy's count, and five wrong guesses from anyone
would refuse everyone. Repeat the check after the first deploy, and after any change in front of
the site, by sending one failed login with a made-up entry:

```bash
curl -s -o /dev/null -H 'X-Forwarded-For: 10.9.9.9' \
  -d 'username=check&password=check' https://<domain>/admin/login
```

The service's log then shows `admin login failed address=... forwarded=[...]`. `address` must be
your real IP address (`curl -s https://api.ipify.org`), and never `10.9.9.9`. If it's instead an
address belonging to a proxy, raise `MAKARIOS_PROXY_HOPS` by one and check again. Too low only
makes visitors share a count, while too high lets them choose their own address.

## Rolling back

In the service's **Deployments** list, open an earlier successful deployment and choose
**Redeploy**. That only rolls back the code. A migration that already ran stays applied, which is
one more reason each migration has to stay compatible with the release before it.

## Admin accounts

Each owner has their own account at `/admin`. Accounts are rows in the production database, so
they're managed from a laptop that connects to it. Copy the database's **public** URL from the
Postgres service's **Variables** (`DATABASE_PUBLIC_URL`) and paste it at a hidden prompt, so it
stays out of your shell history:

```bash
read -rs MAKARIOS_DATABASE_URL && export MAKARIOS_DATABASE_URL   # bash or zsh
read -sx MAKARIOS_DATABASE_URL                                   # fish
uv run python -m app.cli admin-password <name>   # create the account, or set a new password
uv run python -m app.cli admin-remove <name>     # delete it
```

Close the terminal afterwards, so the URL doesn't linger in its environment.

The password is typed at a prompt that doesn't echo, twice, and needs at least 12 characters. A
passphrase of a few words works well. Let each owner type their own password, so nobody else
ever knows it. A new password, or a removed account, signs that owner out everywhere at once.

After five failed logins from one address within 15 minutes, that address is refused until the
oldest failure is 15 minutes old. The count lives in the app's memory, so a redeploy clears it.
Every login, failed login and change made in the admin is written to the service's logs, with
the owner's name.

## Running the tests against Postgres

CI does this on every push. To do it locally, start a throwaway Postgres in Docker and point the
test suite at it:

```bash
docker run -d --rm --name makarios-pg -p 5433:5432 -e POSTGRES_PASSWORD=test postgres:18
MAKARIOS_TEST_DATABASE_URL=postgresql+psycopg://postgres:test@localhost:5433/postgres uv run pytest
docker stop makarios-pg
```

The suite drops and recreates every table, so never point it at a database with data you want.

## Building the image locally

```bash
docker build -t makarios-luxury .
docker run --rm -p 8000:8000 -e PORT=8000 \
  -e MAKARIOS_DATABASE_URL=postgresql://postgres:test@host.docker.internal:5433/makarios \
  makarios-luxury
```

On Linux, add `--network host` and use `localhost` in the URL instead of `host.docker.internal`.
