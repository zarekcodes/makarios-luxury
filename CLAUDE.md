# Makarios Luxury: agent guide

Server-rendered FastAPI site for a luxury watch reseller. Read `docs/ARCHITECTURE.md` for the
stack and structure and `docs/WORKFLOW.md` for process.

## Commands

- Run: `uv run fastapi dev app/main.py` (first time: `uv run alembic upgrade head`, then
  `uv run python -m app.cli seed` for the placeholder watches)
- New migration after a model change: `uv run alembic revision --autogenerate -m "<change>"`,
  then review the file (see `migrations/README`)
- Test: `uv run pytest`
- Lint/format: `uv run ruff check . && uv run ruff format .`
- Add a dependency: `uv add <pkg>` (dev-only: `uv add --dev <pkg>`). Never use pip.

## Rules

- Storefront: no JavaScript frameworks or Node.js. Interactivity is htmx first, Alpine.js only if
  htmx can't do it. (The owner-only areas are the exception: the SQLAdmin admin at `/admin`,
  which ships its own JS, and the planned internal dashboard; see `docs/ARCHITECTURE.md`.)
- Mobile-first: every page must work well at ~400px wide. Performance is the top product priority.
- Routes stay thin; put business logic in `app/services/`.
- Routes that use the database are plain `def`, not `async def`: SQLAlchemy is synchronous here,
  and FastAPI runs a plain `def` on a thread pool.
- HTMX requests (`HX-Request` header) get a partial from `templates/partials/`; normal requests
  get the full page.
- Pages must work without JavaScript (links and forms still function).
- Add or update tests for every behavior change. CI (ruff + pytest) must pass.
- Before you call a change finished, remove the dead code it left behind. Anything your change
  replaced or stopped using goes, in the same commit: functions, classes, routes, services,
  templates and partials, static files, CSS rules, settings, fixtures, tests for behavior that no
  longer exists, and commented-out code. `ruff check` already flags unused imports and variables.
  It can't see the rest, so grep before deleting anything. Templates are referenced by path string
  (`TemplateResponse`, `{% include %}`, `{% extends %}`), and routes and static files through
  `url_for`. Some code is not dead even though nothing calls it yet: code behind a feature flag in
  `app/config.py`, anything under "Built vs. not wired up yet" in `docs/CODEBASE_MAP.md`, and
  Alembic migrations (never delete or edit one that has been applied). Only remove code that this
  change made dead. If you notice older dead code, list it in your summary and don't delete it, so
  each commit stays scoped to its story. When you're done, say what you removed.
- Work happens on the sprint branch (`sprint-6`) in small commits, each leaving CI green and each
  named for the story it belongs to. The commit that finishes a story carries `Closes #N` in its
  body; earlier ones may say `Refs #N`. Work buyers shouldn't see yet goes behind a feature flag
  in `app/config.py`, off by default. `main` changes only through a pull request with every
  required check passing, merged with a merge commit. The backlog and sprints are tracked on the
  GitHub project board (see `docs/WORKFLOW.md`).
- `docs/CODEBASE_MAP.md` is the owner's map of every file and flow, for coming back after time
  away. It is gitignored like the guides below, so it exists only on the owner's machine. When it
  is present, any change that adds, moves, renames or removes a file, wires up something listed
  under "Built vs. not wired up yet", or changes a flow it traces also updates the map. Keep its
  entries short: what the file does and when you'd touch it. When it is absent, carry on without it.
- `docs/LEARNING_GUIDE.md` and `docs/CI_CD_GUIDE.md` are the owner's personal reference notes. They
  are gitignored on purpose, so they exist only on the owner's machine and never appear in a diff or
  a PR. When they are present locally and you add a new folder, pattern, or tool, still update the
  relevant section (and change its `[Sprint N]` label to `[built]`); when they are absent, carry on
  without them.
