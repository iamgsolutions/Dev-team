# Contributing to DEV-TEAM

Welcome — this is the engine that orchestrates an AI software-development team.
It is an **internal tool** for MG + IDA (it is not sold; what we sell is the
software the team builds). Read `docs/QUICKSTART.md` first, then this.

## Dev setup
```powershell
# Python 3.11. From the repo root:
uv venv --python 3.11
uv pip install -e ".[dev]"
.venv\Scripts\python -m pytest -q          # must pass (~150 tests)
```
You do NOT need the brain CLIs (claude/codex/opencode) to develop or test the
engine — their calls are mocked in tests. You only need them to *run* real agents.

## The golden rules
1. **The engine is deterministic on purpose.** Put intelligence in prompts
   (`devteam/roles.py`) and skills (`devteam/skills/*.md`), NOT in orchestration
   code. Orchestration must be predictable and covered by tests.
2. **Keep `pytest` green.** Every behavior change gets a test. If you change an
   operator-facing string, update the test that asserts it.
3. **English everywhere** in the repo — code, comments, prompts, skills, rules,
   docs, and operator notifications. (The only Spanish that stays is inside the
   bilingual command *parsers* kept for backward compatibility; don't "fix" those.)
4. **No secrets, IPs or operator paths in the repo.** Use env vars with sane
   defaults derived from `Path.home()` — never a hardcoded `C:\Users\...`. The
   secrets gate scans every worktree; don't defeat it.
5. **Every state write is atomic** (`storage.atomic_write_json`), **every
   outbound message is secret-redacted** (`storage.redact`), **every subprocess
   has a timeout.** Follow these patterns when you add code.

## Workflow
1. **Branch + PR per task** (`task/<slug>` or `feat/<slug>`). One intention per PR.
2. **Conventional commits** in English: `feat:`, `fix:`, `test:`, `docs:`,
   `chore:`, `refactor:`.
3. **PR description**: What / Why / How to test. List risks and any debt you leave.
4. Run `.venv\Scripts\python -m devteam.cli doctor` before opening a PR if your
   change touches CLIs, credentials, or the daemon.

## Where to start
- New here? Pick something from **`docs/STARTER-TASKS.md`** (scoped first issues
  mapped to the roadmap, sorted by difficulty).
- Want the big picture of how work is dispatched? **`docs/05-EXECUTION-POLICY.md`**.
- Adding a skill / role / preset / MCP / brain? **`docs/02-EXTENDING.md`**.
- Lost in the code? **`docs/06-GLOSSARY.md`** maps every concept → file → test.

## What to read for the full picture
`docs/README.md` is the index. The reading order there takes you from a 10-minute
first run to the architecture and the roadmap.
