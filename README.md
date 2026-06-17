# DEV-TEAM — autonomous multi-agent software development engine

An autonomous, multi-agent software development organization, built by MG
Solutions. A director agent (Hermes) breaks a project brief into tasks; a team
of AI brains (Claude Code / Codex / OpenCode / Gemini) design, build, test,
audit and deploy it — under a deterministic engine that enforces process,
quality, budget, isolation and memory.

**The thesis:** the director sustains the system, but the software is built by
the COLLECTIVE — no single model does the work; the system does.

## Documentation

Full docs in **[`docs/`](docs/)**:
- [Overview](docs/00-OVERVIEW.md) — what it is, how advanced it is, the goal.
- [Architecture](docs/01-ARCHITECTURE.md) — how it's programmed, with diagrams.
- [Extending](docs/02-EXTENDING.md) — add skills, roles, presets, MCPs, brains.
- [Roadmap](docs/03-ROADMAP.md) — the complex build plan.
- [Collaboration](docs/04-COLLABORATION.md) — repos, workflow, onboarding.

## Structure
- `devteam/` — the package. Core: `state`, `budget`, `instruction` (5-block),
  `router`, `executor` (the spine), `brains/` (CLI invokers), `worktree`,
  `memory` (handoff), `pipeline`, `gates`, `audit`, `reflective` (scorecard),
  `daemon`, `discord_listener`, `doctor`, `catalog`, `eventlog`, `presets`, `cli`.
- `devteam/skills/` — senior-craft skill packs injected into agents.
- `tests/` — pytest (engine logic; brain CLIs are mocked).
- `data/` — runtime state (gitignored; never committed).

## CLI
```
devteam new-project <brief.md> [--name X] [--cap 30]   # start a project
devteam adopt <repo-path>                              # adopt an existing repo
devteam status | panel | log | scorecard | doctor      # observe
devteam presets | catalog | skills                     # inspect the harness
devteam run-phase <name> | approve <name>              # drive the pipeline
devteam daemon --interval 60                            # 24/7 loop
```

## Development
```
# Python 3.11
uv venv && uv pip install -e ".[dev]"
.venv\Scripts\python -m pytest -q
```
Conventions: English everywhere (code, comments, agent prompts, skills, docs).
No secrets, IPs or operator paths in the repo — use environment variables.
The engine is deterministic; intelligence lives in prompts and skills.
