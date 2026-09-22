# Sprint 1: Foundations

**Dates:** 2026-09-14 – 2026-09-21
**Sprint goal:** A version-controlled, tested project skeleton with a defined MVP, architecture, and
backlog, ready for feature work in Sprint 2.

## Committed stories

| Story | Points | Status |
| --- | --- | --- |
| Project scaffolding (FastAPI app, tests, CI, lint) | 3 | Done |
| MVP and architecture docs | 2 | Done |
| Backlog and roadmap | 2 | Done |

**Committed: 7 points. Completed: 7.**

## Sprint review

_What shipped:_

- **A running FastAPI app.** App factory in `app/main.py`, settings from environment variables via
  `app/config.py`, page routes and JSON routes split into `app/routes/`, and Jinja templates wired
  up. `/` returns HTML and `/api/health` returns `{"status": "ok"}`.
- **A working test suite.** `tests/test_smoke.py` covers the health endpoint and the home page
  rendering, using FastAPI's `TestClient`.
- **Continuous integration.** `.github/workflows/ci.yml` runs Ruff lint, a formatting check and
  pytest on every push and pull request, installing with `uv sync --locked` so CI uses exactly the
  locked dependency versions.
- **The planning documents:** `MVP.md` (scope and the "done" definition), `ARCHITECTURE.md` (stack
  choices and the reasoning), `WORKFLOW.md` (sprint process and Definition of Done) and
  `BACKLOG.md` (the roadmap through Sprint 7).
- **Repository setup:** issue and pull request templates, `.gitignore`, and `.env.example`.

_Not done:_ the GitHub Projects board was planned but not set up; the backlog currently lives in
`docs/BACKLOG.md` instead.

## Retrospective

**What went well:**

**What didn't:**

**One change for Sprint 2:**
