# Makarios Luxury

Website for Makarios Luxury, a reseller of authenticated pre-owned luxury watches. Buyers browse
inventory and send inquiries; the owner manages listings from an admin area.

Built as a semester project for Development Processes & Methodologies using Agile (Scrum-style,
1–2 week sprints).

**Stack:** FastAPI · Jinja2 · htmx · Tailwind CSS · SQLAlchemy + Alembic · pytest · GitHub Actions

## Getting started

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync                          # install dependencies into .venv
cp .env.example .env             # local settings
uv run alembic upgrade head      # create the local SQLite database, makarios.db
uv run python -m app.cli seed    # load the placeholder watches
uv run fastapi dev app/main.py   # start with auto-reload at http://127.0.0.1:8000
```

While working on templates or styles, run the Tailwind watcher in a **second terminal** so the CSS
rebuilds every time you save:

```bash
./scripts/tailwind.sh --watch
```

The script downloads the pinned Tailwind standalone binary into `bin/` (gitignored) on first use.
There is no Node.js and no `package.json` in this project.

API docs are auto-generated at http://127.0.0.1:8000/docs (development only; production hides
them).

## Common commands

```bash
uv run pytest                    # run tests (on SQLite; see docs/DEPLOY.md for Postgres)
uv run ruff check .              # lint
uv run ruff format .             # auto-format
./scripts/tailwind.sh            # rebuild the CSS (commit the result)
```

The database schema changes only through migrations in `migrations/versions/`:

```bash
uv run alembic upgrade head                           # apply new migrations (after a pull, too)
uv run alembic revision --autogenerate -m "<change>"  # after changing a model; review the file
```

A test fails if a model changes without its migration. See `migrations/README` for what to check
in a generated file.

The owners manage watches at http://127.0.0.1:8000/admin. Create a local account first:

```bash
uv run python -m app.cli admin-password <name>    # prompts for the password; also resets it
uv run python -m app.cli admin-remove <name>      # delete an account
```

A watch's status can also be set from the command line:

```bash
uv run python -m app.cli status aurelian-meridian-chronograph on-hold   # or available, or sold
```

`app/static/css/app.css` is generated but committed, because the deployed server has no Tailwind
binary. CI rebuilds it and fails if the committed file is out of date, so run the command above and
commit the result whenever you change a template or `input.css`.

The output is always minified, in watch mode too, so the file on disk is the same whichever command
produced it. Without that, an ordinary development session would leave an unminified stylesheet
staged and CI would reject it.

Asset generators, only needed when the source material changes:

```bash
uv run python scripts/build_brand_assets.py        # logo badge + favicons from design/
```

## Documentation

- [Brand](docs/BRAND.md): palette, type, layout rules, and how to swap in a new logo
- [MVP definition](docs/MVP.md): vision, users, and what's in and out of scope
- [Architecture](docs/ARCHITECTURE.md): stack choices, structure, and open decisions
- [Deploying](docs/DEPLOY.md): Railway setup, production variables, migrations, rollback
- [Workflow](docs/WORKFLOW.md): sprint process, board, branching, Definition of Done
- [Roadmap and epics](docs/BACKLOG.md): the sprint-by-sprint plan; the backlog itself is the
  [project board](https://github.com/users/zarekcodes/projects/2)
- [Sprint notes](docs/sprints/): per-sprint goals, reviews, and retrospectives
