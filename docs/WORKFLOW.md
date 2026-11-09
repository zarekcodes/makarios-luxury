# Development Workflow

This project follows **Scrum-style Agile**, adapted for a solo developer, with **1–2 week sprints**.

## Sprint cadence

| Event | When | Output |
| --- | --- | --- |
| **Sprint planning** | First day of the sprint | Sprint goal in `docs/sprints/sprint-NN.md`; stories moved into the sprint on the board, each estimated in story points; the last sprint's unfinished stories moved in or back to the backlog. Then the **start-of-sprint screenshot**. |
| **Daily progress** | Each work session | Move cards on the board; keep issues updated. |
| **Sprint review** | Last day | Demo the working increment; record what shipped in `sprint-NN.md`; make the sprint's final merge into `main` and delete the sprint branch. Then the **end-of-sprint screenshot**, before anything moves to the next sprint. |
| **Retrospective** | Last day | What went well / what didn't / one thing to change next sprint. |
| **Backlog refinement** | Mid-sprint | Split, clarify, and re-prioritize upcoming stories. |

## Tooling: a GitHub project board plus the repository

- **Backlog and sprints** = the [project board](https://github.com/users/zarekcodes/projects/2).
  Every story is an issue, filed as a sub-issue of its epic; a story split into technical slices
  gets tasks as its own sub-issues. Each item has a **Status** (Todo, In Progress, Done), a
  **Sprint** (an iteration with the sprint's dates) and **Points**. An open story with no sprint is
  in the backlog. The views:
  - *Sprint board*: the current sprint, one column per status, with points summed per column.
  - *Backlog*: open stories not yet in a sprint, grouped by epic.
  - *Velocity*: every story that was in a sprint, grouped by sprint, with points summed.
  - *Epics*: each epic's progress through its stories.
- **Roadmap** = `docs/BACKLOG.md`: the sprint-by-sprint plan and a summary of each epic.
- **Sprint plan and decisions** = `docs/sprints/sprint-NN.md`: the goal, the stories with their
  issue numbers, and the decisions made during the sprint. The board shows what happened and when;
  this file records why.
- **Board screenshots** = one after sprint planning and one at the sprint review, saved as
  `docs/sprints/local/sprint-NN-start.png` and `sprint-NN-end.png`. The course's retrospective
  asks for both. Each shows the board as it actually was, so unfinished stories stay in their
  sprint for the end screenshot and move only at the next planning.
- **Sprint review and retrospective** = `docs/sprints/local/`, which is gitignored. They are the
  owner's written reflection and feed coursework submissions, so they stay off the repository.
- **Progress** = the commits on the sprint branch, one per story, each closing its issue.
- **Estimates** = story points, Fibonacci (1, 2, 3, 5, 8), agreed at sprint planning.

Sprints 1–3 were tracked in the repository alone, because a board looked like extra bookkeeping
for one person. The board was adopted on the last day of Sprint 3, because the course's retrospective
asks for board screenshots, and Sprints 1–3 were backfilled from their sprint files. Each
backfilled issue says so, because GitHub's created and closed dates show the backfill rather than
when the work was done.

## Definition of Ready

A story can enter a sprint when its issue has a user-story statement, acceptance criteria, and an
estimate in its Points field, and it's small enough to finish within one sprint.

## Definition of Done

- Acceptance criteria met
- Tests added or updated; CI passes (lint, format, tests)
- Works at phone width (~400px) and desktop
- Committed to the sprint branch as small, clearly named commits, each leaving CI green
- On `main` through a pull request, and visible to buyers: any feature flag it was built behind
  is removed
- Docs updated if behavior or setup changed

## Branching and commits (GitHub Flow, sprint-scoped)

- `main` is always working and always deployable: Railway deploys every merge into it. Nothing is
  committed to it directly. The **Protect main** ruleset enforces that (see
  [DEPLOY.md](DEPLOY.md#which-branch)).
- **One branch per sprint**, named for the sprint (`sprint-6`), kept for the whole sprint.
- **Small commits.** A story lands as one commit or several. Each is small enough to review and
  revert on its own, and each leaves CI green, so any one of them is safe to deploy. Work buyers
  shouldn't see yet goes behind a feature flag that's off by default (the catalog page's
  `MAKARIOS_CATALOG_PAGE_ENABLED` in `app/config.py` is the first), and the flag is removed when
  the story is done.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):
  `feat: add watch detail page`, `fix: ...`, `docs: ...`, `test: ...`, `chore: ...`
- Name the story in each commit's subject line, so the sprint reads story by story. The commit
  that **finishes** a story puts `Closes #12` in its body; earlier commits for the same story can
  say `Refs #12`, which lists them on the issue without closing it. The issue closes, and its card
  moves to Done, when the closing commit reaches `main`.
- **Merge often.** Whenever the sprint branch holds green work worth deploying, open a pull request
  from it into `main` and fill in the template; don't wait for the sprint review. The ruleset
  requires every CI check to pass and allows only a merge commit (no squash or rebase), so every
  commit survives on `main`. After the merge, keep working on the same branch. The next pull
  request from it carries only the newer commits.
- Delete the sprint branch after the sprint's final merge, at the review.
- **Dependabot** opens its own pull requests into `main` when a dependency has a known
  vulnerability. Read the changelog for a major-version bump, merge once CI passes, then bring the
  change into the sprint branch (`git merge origin/main`) so `uv.lock` doesn't conflict later.

### Why one branch per sprint

A per-issue branch is the right default for a team, where several people need to work without
tripping over each other. On a solo project the cost is real and the benefit is not: the landing
page's header, hero and footer are visually interdependent, so separate branches would mean
reviewing half-styled pages and rebasing repeatedly.

Traceability is what actually matters for this project, and it survives: every commit names its
story, and the one that finishes it closes its issue.

### Why merge often

Until Sprint 6 the sprint branch merged into `main` only at the review, so each sprint reached
production as one large deploy. Merging green work as it lands keeps the sprint branch close to
production, so each deploy is small and a problem points to a few commits instead of a whole
sprint. The cost is that unfinished work reaches `main` too, which is what feature flags are for.
The first mid-sprint merge was [#71] on 2026-11-08.

[#71]: https://github.com/zarekcodes/makarios-luxury/pull/71

## Agentic coding (Claude Code)

AI-assisted work goes through the same process as hand-written work: it's scoped to an issue,
done on a branch, reviewed by me in the PR, and must pass CI. `CLAUDE.md` gives the agent the
project's conventions. Note in the PR description when a change was substantially AI-generated.
