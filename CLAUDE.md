# Makarios Luxury: agent guide

Server-rendered FastAPI site for a luxury watch reseller. Read `docs/ARCHITECTURE.md` for the
stack and structure and `docs/WORKFLOW.md` for process.

## Commands

- Run: `uv run fastapi dev app/main.py`
- Test: `uv run pytest`
- Lint/format: `uv run ruff check . && uv run ruff format .`
- Add a dependency: `uv add <pkg>` (dev-only: `uv add --dev <pkg>`). Never use pip.

## Rules

- Storefront: no JavaScript frameworks or Node.js. Interactivity is htmx first, Alpine.js only if
  htmx can't do it. (The planned internal dashboard is the one exception; see `docs/ARCHITECTURE.md`.)
- Mobile-first: every page must work well at ~400px wide. Performance is the top product priority.
- Routes stay thin; put business logic in `app/services/`.
- HTMX requests (`HX-Request` header) get a partial from `templates/partials/`; normal requests
  get the full page.
- Pages must work without JavaScript (links and forms still function).
- Add or update tests for every behavior change. CI (ruff + pytest) must pass.
- Work happens on a sprint branch (`sprint-2`, `sprint-3`), one commit per story, named for the
  story it implements. Never commit directly to `main`.
- `docs/LEARNING_GUIDE.md` and `docs/CI_CD_GUIDE.md` are the owner's personal reference notes. They
  are gitignored on purpose, so they exist only on the owner's machine and never appear in a diff or
  a PR. When they are present locally and you add a new folder, pattern, or tool, still update the
  relevant section (and change its `[Sprint N]` label to `[built]`); when they are absent, carry on
  without them.
