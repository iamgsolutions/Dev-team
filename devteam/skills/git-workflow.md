# SKILL: Git workflow — branches, commits and PRs consistent across the team

### Branches
- The engine creates your branch (`task/<slug>`); work ONLY on it, never on main.
- One branch = one task = one intent. Don't mix features.

### Commits
- Conventional: `feat:`, `fix:`, `test:`, `docs:`, `chore:`, `refactor:`,
  `perf:`. In English, imperative, first line < 72 chars.
- Atomic: each commit leaves the repo compiling and coherent. Separate "behavior
  change" from "shape change" (refactor) into distinct commits.
- The body explains the WHY when it isn't obvious. The engine adds the
  `Model:`/`Role:` trailer automatically — don't duplicate it.

### Pull Requests (when published on GitHub)
- Title = the change in one line. Body with 3 sections:
  **What** (I changed), **Why** (reason/issue), **How to test it** (steps/tests).
- List known risks and any debt you leave behind.
- Small, focused PR > giant PR. If it touches >15 non-trivial files, it probably
  should have been split.

### What goes where
- In the COMMIT: the change and its technical why.
- In NOTES.md: decisions, open questions, heads-ups for the next agent, tech debt.
- In docs/adr/: architecture decisions that aren't reopened without discussion.
- NEVER in git: secrets (.env), build artifacts, dependencies (node_modules).
