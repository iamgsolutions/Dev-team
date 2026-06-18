# DEV-TEAM documentation

An autonomous multi-agent software development organization, built by MG Solutions
as an internal tool for MG + IDA.

**Start here:** **[QUICKSTART.md](QUICKSTART.md)** — clone to first running phase in
~10 minutes.

Then read in order:

1. **[00-OVERVIEW.md](00-OVERVIEW.md)** — what it is, the thesis, the loop, how
   advanced it is (honest %), and the end goal.
2. **[05-EXECUTION-POLICY.md](05-EXECUTION-POLICY.md)** — **exactly which brain and
   model runs for each task at each moment**, rations, cost, failure handling. The
   single source of truth for how the system works.
3. **[01-ARCHITECTURE.md](01-ARCHITECTURE.md)** — how it's programmed, module by
   module, with diagrams and the exact path of one task.
4. **[06-GLOSSARY.md](06-GLOSSARY.md)** — vocabulary + a concept → file → test map
   to navigate the code cold.
5. **[02-EXTENDING.md](02-EXTENDING.md)** — how to add skills, roles, agent
   presets, MCPs and brains.
6. **[03-ROADMAP.md](03-ROADMAP.md)** — the complex features to build (the
   "monster" plan), with complexity/value and ownership.
7. **[04-COLLABORATION.md](04-COLLABORATION.md)** — how we work together (repos,
   English-only, workflow, onboarding).

For contributors:
- **[../CONTRIBUTING.md](../CONTRIBUTING.md)** — dev setup, golden rules, workflow.
- **[STARTER-TASKS.md](STARTER-TASKS.md)** — scoped first issues mapped to the
  roadmap, sorted by difficulty.

Reference notes:
- **[jcode.md](jcode.md)** — evaluation of the jcode brain (why it's integrated,
  risks, how it's wired, and the benchmark plan before promoting it).

## TL;DR for a new developer
- Python 3.11. `uv venv && uv pip install -e ".[dev]"` then `pytest -q` (must pass).
- The engine is in `devteam/`. The spine is `executor.py`; the flow is `pipeline.py`.
- The engine is deterministic; intelligence lives in prompts (`roles.py`) and
  skills (`skills/*.md`). Keep tests green, English everywhere, no secrets in the repo.
