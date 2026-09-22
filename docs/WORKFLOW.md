# Development Workflow

This project follows **Scrum-style Agile**, adapted for a solo developer, with **1–2 week sprints**.

## Sprint cadence

| Event | When | Output |
| --- | --- | --- |
| **Sprint planning** | First day of the sprint | Sprint goal + stories pulled from the backlog into the sprint, each estimated in story points. |
| **Daily progress** | Each work session | Move cards on the board; keep issues updated. |
| **Sprint review** | Last day | Demo the working increment; record what shipped in `docs/sprints/sprint-NN.md`. |
| **Retrospective** | Last day | What went well / what didn't / one thing to change next sprint. |
| **Backlog refinement** | Mid-sprint | Split, clarify, and re-prioritize upcoming stories. |

## Tooling: the repository itself

Tracking lives in the repo rather than in a separate tool, so the plan and the code stay in one
place and the process is visible in the history.

- **Backlog** = `docs/BACKLOG.md`, grouped into epics and a sprint-by-sprint roadmap.
- **Sprint plan** = `docs/sprints/sprint-NN.md`: the goal, the committed stories, and their
  estimates, written at the start of the sprint.
- **Progress** = the commits on the sprint branch, one per story.
- **Estimates** = story points, Fibonacci (1, 2, 3, 5, 8), agreed at sprint planning.

GitHub Issues and a Projects board would add a status column and a burndown chart. They are worth
adopting if the backlog outgrows a single file, or if the course requires them; the issue templates
in `.github/ISSUE_TEMPLATE/` are already there for that. Until then they would be extra
bookkeeping for one person with no extra information.

## Definition of Ready

A story can enter a sprint when it has a user-story statement, acceptance criteria, and an
estimate, and it's small enough to finish within one sprint.

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
- Name the story a commit implements in its subject line, so the sprint reads story by story. If
  the backlog ever moves to GitHub Issues, add `Closes #12` to the commit body as well.
- Open one pull request per sprint branch, fill in the template, and **merge without squashing**,
  so the per-story commits survive on `main`.
- Delete the branch after merging.

### Why one branch per sprint

A per-issue branch is the right default for a team, where several people need to work without
tripping over each other. On a solo project the cost is real and the benefit is not: the landing
page's header, hero and footer are visually interdependent, so separate branches would mean
reviewing half-styled pages and rebasing repeatedly.

Traceability is what actually matters for this project, and it survives: one commit per story,
each naming its issue. The unit of review becomes the sprint rather than the story, which is also
how the sprint review reads.

## Agentic coding (Claude Code)

AI-assisted work goes through the same process as hand-written work: it's scoped to an issue,
done on a branch, reviewed by me in the PR, and must pass CI. `CLAUDE.md` gives the agent the
project's conventions. Note in the PR description when a change was substantially AI-generated.
