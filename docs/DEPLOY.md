# Deploying

Production runs on [Railway](https://railway.com) (Hobby plan): one service built from this
repository's `Dockerfile`, and one Railway Postgres database. Railway deploys on every push to the
branch the service follows, once CI passes. The choice of host is recorded in
[Sprint 5's decisions](sprints/sprint-05.md#decisions-made-this-sprint).

## What happens on a deploy

1. A push reaches the branch the service follows. With **Wait for CI** on, Railway waits until
   GitHub Actions (lint, tests on SQLite and on Postgres, the CSS check) has passed.
2. Railway builds the image from `Dockerfile`. `railway.toml` tells it to.
3. **Pre-deploy:** `alembic upgrade head` runs in the new image, against the production database.
   If it fails, the deploy stops there and the previous version keeps serving.
4. The new container starts (`fastapi run`, on the port Railway assigns through `$PORT`).
5. Railway calls `/api/health` until it answers 200, then moves traffic to the new version and
   stops the old one. A version that never becomes healthy never takes traffic.

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
| `MAKARIOS_SECRET_KEY` | the output of `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` | Signs the admin's session cookie. Anyone who has it can forge a login, so it lives only here. |

Railway sets `PORT` itself. `MAKARIOS_DEBUG` defaults to off. The app refuses to start in
production if debug is on, or if the secret key is missing or shorter than 32 characters.
Changing the secret key signs every owner out, which also makes it the emergency logout.

## First-time setup

1. Create a Railway account and sign in with GitHub. The trial credit covers the first deploy.
   Move to the Hobby plan ($5 a month) before the credit runs out.
2. **New Project → Deploy from GitHub repo →** `zarekcodes/makarios-luxury`. Give Railway access
   to this repository only.
3. In the service's **Settings → Source**, set the branch (see [Which branch](#which-branch)) and
   turn on **Wait for CI**.
4. In the project, **Create → Database → PostgreSQL**. Leave its name as `Postgres`, since the
   variable reference above uses it.
5. Set the variables above on the app service, then deploy.
6. **Settings → Networking → Generate Domain** for the public `*.up.railway.app` HTTPS URL.

## Which branch

During Sprint 5 the service follows **`sprint-5`**, because the site had to go live within the
sprint, and the sprint's work reaches `main` only when its pull request merges at the sprint
review. Once that pull request merges, switch the service's branch to **`main`** and leave it
there. From then on, production is whatever `main` holds.

## Checking a deploy

```bash
curl -s https://<domain>/api/health   # {"status":"ok"}
```

Then load the home page on a phone, and run PageSpeed Insights (mobile) on the URL. The target is
a performance score of 90 or above.

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

The password is typed at a prompt that doesn't echo, twice, and needs at least 12 characters. A
passphrase of a few words works well. Let each owner type their own password, so nobody else
ever knows it. A new password, or a removed account, signs that owner out everywhere at once.

After five failed logins from one address within 15 minutes, that address is refused until the
oldest failure is 15 minutes old. The count lives in the app's memory, so a redeploy clears it.
Every login, failed login and change made in the admin is written to the service's logs, with
the owner's name.

## Rolling back

In the service's **Deployments** list, open an earlier successful deployment and choose
**Redeploy**. That only rolls back the code. A migration that already ran stays applied, which is
one more reason each migration has to stay compatible with the release before it.

## Running the tests against Postgres

CI does this on every push. To do it locally, start a throwaway Postgres in Docker and point the
test suite at it:

```bash
docker run -d --rm --name makarios-pg -p 5433:5432 -e POSTGRES_PASSWORD=test postgres:17
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
