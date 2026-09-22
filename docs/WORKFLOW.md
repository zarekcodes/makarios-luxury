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

## Tooling: GitHub Projects

- **Backlog** = GitHub Issues using the *User story* template. `docs/BACKLOG.md` is the seed list.
- **Board columns:** Backlog → Sprint (Ready) → In Progress → In Review → Done
- **Sprints** = the Project's *Iteration* field (set the length to match the sprint).
- **Estimates** = a *Story Points* number field (Fibonacci: 1, 2, 3, 5, 8).
- **Labels:** `story`, `bug`, `chore`, `docs`, plus an epic label (e.g. `epic:catalog`).

## Definition of Ready

A story can enter a sprint when it has a user-story statement, acceptance criteria, and an
estimate, and it's small enough to finish within one sprint.

## Definition of Done

- Acceptance criteria met
- Tests added or updated; CI passes (lint, format, tests)
- Works at phone width (~400px) and desktop
- Committed to the sprint branch, with `Closes #N` in the commit body
- Reaches `main` when the sprint branch is merged through its pull request
- Docs updated if behavior or setup changed

## Branching and commits (GitHub Flow, sprint-scoped)

- `main` is always working. Never commit directly to it.
- **One branch per sprint**, named for the sprint: `sprint-2`, `sprint-3`.
- **One commit per story**, so each story stays individually reviewable and revertable, and the
  sprint's work can still be read story by story in `git log`.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):
  `feat: add watch detail page`, `fix: ...`, `docs: ...`, `test: ...`, `chore: ...`
- Reference the issue a commit closes in its body (`Closes #12`), so merging the sprint branch
  closes every story it completed.
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
