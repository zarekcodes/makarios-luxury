# Makarios Luxury: agent guide

Server-rendered FastAPI site for a luxury watch reseller. Read `docs/ARCHITECTURE.md` for the
stack and structure and `docs/WORKFLOW.md` for process.

## Commands

- Run: `uv run fastapi dev app/main.py`
- Test: `uv run pytest`
- Lint/format: `uv run ruff check . && uv run ruff format .`
- Add a dependency: `uv add <pkg>` (dev-only: `uv add --dev <pkg>`). Never use pip.

## Rules

- No JavaScript frameworks or Node.js. Interactivity is htmx first, Alpine.js only if htmx can't do it.
- Mobile-first: every page must work well at ~400px wide. Performance is the top product priority.
- Routes stay thin; put business logic in `app/services/`.
- HTMX requests (`HX-Request` header) get a partial from `templates/partials/`; normal requests
  get the full page.
- Pages must work without JavaScript (links and forms still function).
- Add or update tests for every behavior change. CI (ruff + pytest) must pass.
- Work happens on a branch tied to a GitHub issue; never commit directly to `main`.
