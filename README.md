# Makarios Luxury

Website for Makarios Luxury, a reseller of authenticated pre-owned luxury watches. Buyers browse
inventory and send inquiries; the owner manages listings from an admin area.

Built as a semester project for Development Processes & Methodologies using Agile (Scrum-style,
1–2 week sprints).

**Stack:** FastAPI · Jinja2 · htmx · Tailwind CSS · SQLAlchemy · pytest · GitHub Actions

## Getting started

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync                          # install dependencies into .venv
cp .env.example .env             # local settings
uv run fastapi dev app/main.py   # start with auto-reload at http://127.0.0.1:8000
```

While working on templates or styles, run the Tailwind watcher in a **second terminal** so the CSS
rebuilds every time you save:

```bash
./scripts/tailwind.sh --watch
```

The script downloads the pinned Tailwind standalone binary into `bin/` (gitignored) on first use.
There is no Node.js and no `package.json` in this project.

API docs are auto-generated at http://127.0.0.1:8000/docs.

## Common commands

```bash
uv run pytest                    # run tests
uv run ruff check .              # lint
uv run ruff format .             # auto-format
./scripts/tailwind.sh --minify   # rebuild the CSS (commit the result)
```

`app/static/css/app.css` is generated but committed, because the deployed server has no Tailwind
binary. CI rebuilds it and fails if the committed file is out of date, so run the command above and
commit the result whenever you change a template or `input.css`.

Asset generators, only needed when the source material changes:

```bash
uv run python scripts/build_brand_assets.py        # logo badge + favicons from design/
```

## Documentation

- [Brand](docs/BRAND.md): palette, type, layout rules, and how to swap in a new logo
- [Learning guide](docs/LEARNING_GUIDE.md): how the pieces fit together and why things live where they do. **Start here if you're new to the codebase.**
- [CI/CD guide](docs/CI_CD_GUIDE.md): how the automated checks work, what to do when they fail, and how deployment will work
- [MVP definition](docs/MVP.md): vision, users, and what's in and out of scope
- [Architecture](docs/ARCHITECTURE.md): stack choices, structure, and open decisions
- [Workflow](docs/WORKFLOW.md): sprint process, board, branching, Definition of Done
- [Backlog seed](docs/BACKLOG.md): roadmap and initial user stories
- [Sprint notes](docs/sprints/): per-sprint goals, reviews, and retrospectives
