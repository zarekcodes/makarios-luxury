# Development Workflow

This project follows **Scrum-style Agile**, adapted for a solo developer, with **1–2 week sprints**.

## Sprint cadence

| Event | When | Output |
| --- | --- | --- |
| **Sprint planning** | First day of the sprint | Sprint goal in `docs/sprints/sprint-NN.md`; stories moved into the sprint on the board, each estimated in story points; the last sprint's unfinished stories moved in or back to the backlog. Then the **start-of-sprint screenshot**. |
| **Daily progress** | Each work session | Move cards on the board; keep issues updated. |
| **Sprint review** | Last day | Demo the working increment; record what shipped in `sprint-NN.md`; merge the sprint's pull request, which closes its issues. Then the **end-of-sprint screenshot**, before anything moves to the next sprint. |
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
- Committed to the sprint branch as a single, clearly named commit
- Reaches `main` when the sprint branch is merged through its pull request
- Docs updated if behavior or setup changed

## Branching and commits (GitHub Flow, sprint-scoped)

- `main` is always working. Never commit directly to it.
- **One branch per sprint**, named for the sprint: `sprint-2`, `sprint-3`.
- **One commit per story**, so each story stays individually reviewable and revertable, and the
  sprint's work can still be read story by story in `git log`.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):
  `feat: add watch detail page`, `fix: ...`, `docs: ...`, `test: ...`, `chore: ...`
- Name the story a commit implements in its subject line, so the sprint reads story by story, and
  put `Closes #12` for its issue in the commit body. The issue closes, and its card moves to Done,
  when the sprint's pull request merges into `main`: the moment the Definition of Done counts it
  as done.
- Open one pull request per sprint branch, fill in the template, and **merge without squashing**,
  so the per-story commits survive on `main`.
- Delete the branch after merging.

### Why one branch per sprint

A per-issue branch is the right default for a team, where several people need to work without
tripping over each other. On a solo project the cost is real and the benefit is not: the landing
page's header, hero and footer are visually interdependent, so separate branches would mean
reviewing half-styled pages and rebasing repeatedly.

Traceability is what actually matters for this project, and it survives: one commit per story,
each closing its issue. The unit of review becomes the sprint rather than the story, which is also
how the sprint review reads.

## Agentic coding (Claude Code)

AI-assisted work goes through the same process as hand-written work: it's scoped to an issue,
done on a branch, reviewed by me in the PR, and must pass CI. `CLAUDE.md` gives the agent the
project's conventions. Note in the PR description when a change was substantially AI-generated.
