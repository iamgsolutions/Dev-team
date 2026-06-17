# Collaboration model (MG ↔ IDA)

> How we work together on DEV-TEAM. The goal: IDA's specialists add the complex,
> heavy-engineering pieces (parallelism, testing infra, deploy, security) while
> MG drives the orchestration intelligence and product direction.

## Repositories

| Repo | What | Who | Language |
|---|---|---|---|
| **`Dev-team`** (this repo) | The engine + agent team + skills + docs. NO secrets, NO private data. | Shared with IDA | **English (100%)** |
| `memoria-desarrollo-hermes` (private) | MG's operational memory, business context, deployment specifics, chat history. | MG only | Spanish |

This repo is the clean, shareable product. It must never contain API keys,
tokens, customer data, server IPs or operator paths — those live outside it
(env vars / the private repo). The built-in secret scanner + redaction enforce
this, but contributors must respect it too.

## Language: English everywhere in this repo
All code, comments, agent prompts, skills, rules, docs **and operator
notifications** (the Discord milestones/blockers) are English. The only Spanish
that remains is inside a few command **parsers** kept bilingual on purpose, so
existing Spanish projects/briefs still work (audit verdicts, the Discord command
words, brief headings, the STATE header). Everything a human or an agent *reads*
is English.

## Scope: the agent system is internal (MG + IDA)
The orchestrator is an **internal tool** for MG and IDA — it is not sold to
clients. What gets sold is the *software the team builds*. This is why
multi-tenant/client-isolation is out of scope (see `03-ROADMAP.md` item K) and
why sandboxing (item I) is framed as internal safety, not a sales gate.

## Workflow
1. **Branch + PR per task** (`task/<slug>` or `feat/<slug>`). One intention per PR.
2. **Keep `pytest` green.** Every behavior gets a test. The engine is
   deterministic — orchestration changes must be predictable and covered.
3. **Conventional commits** in English (`feat:`, `fix:`, `test:`, `docs:`...).
4. **Don't put intelligence in orchestration code.** Intelligence lives in
   prompts/skills; orchestration stays deterministic and tested.
5. **PR description**: What / Why / How to test. List risks and debt.

## Dev environment
```
# Python 3.11. From the repo root:
uv venv && uv pip install -e ".[dev]"
.venv\Scripts\python -m pytest -q          # must pass

# The coding-agent CLIs (claude/codex/opencode/gemini) are needed only to RUN
# agents, not to develop/test the engine (their calls are mocked in tests).
```

## What we need from IDA first (proposed)
See `03-ROADMAP.md`. The highest-value pieces for IDA's specialists:
- **A** — intra-project parallelism + distributed worker queue.
- **C** — real testing infrastructure (API tester + Playwright E2E harness).
- **I** — agent sandboxing & supply-chain/SAST security.
- **D** — real autonomous deploy (CD, reverse proxy, blue-green, backups).

MG will drive **B** (smart task-graph decomposition) and **F** (the Solution
Architect Agent / productization) in parallel.

## Onboarding path for an IDA developer
1. Read `docs/00-OVERVIEW.md` → `01-ARCHITECTURE.md` → `02-EXTENDING.md`.
2. Set up the dev env, run the tests.
3. Read `devteam/executor.py` (the spine) and `devteam/pipeline.py` (the flow).
4. Pick a roadmap item; propose a design PR before building.
