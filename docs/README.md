# DEV-TEAM documentation

An autonomous multi-agent software development organization, built by MG Solutions.

Read in order:

1. **[00-OVERVIEW.md](00-OVERVIEW.md)** — what it is, the thesis, the loop, how
   advanced it is (honest %), and the end goal.
2. **[01-ARCHITECTURE.md](01-ARCHITECTURE.md)** — how it's programmed, module by
   module, with diagrams and the exact path of one task.
3. **[02-EXTENDING.md](02-EXTENDING.md)** — how to add skills, roles, agent
   presets, MCPs and brains.
4. **[03-ROADMAP.md](03-ROADMAP.md)** — the complex features to build (the
   "monster" plan), with complexity/value and ownership.
5. **[04-COLLABORATION.md](04-COLLABORATION.md)** — how we work together (repos,
   English-only, workflow, onboarding).

## TL;DR for a new developer
- Python 3.11. `uv venv && uv pip install -e ".[dev]"` then `pytest -q` (must pass).
- The engine is in `devteam/`. The spine is `executor.py`; the flow is `pipeline.py`.
- The engine is deterministic; intelligence lives in prompts (`roles.py`) and
  skills (`skills/*.md`). Keep tests green, English everywhere, no secrets in the repo.
