# Starter tasks for IDA

Scoped, real work to get productive fast — sorted by size. Each task lists the
files to touch and the roadmap item it advances (see `03-ROADMAP.md`). Every
change must keep `pytest` green and add a test for new behavior. Pick one, open a
`task/<slug>` branch, propose a short design in the PR before building anything big.

## Good first issues (½–1 day) — learn the codebase

1. **More secret patterns in the gate.** Add Google API keys, Stripe `sk_live_…`,
   JWTs, and generic `AWS_SECRET` patterns to `SECRET_PATTERNS` in
   `devteam/gates.py`; add cases to `tests/test_audit.py`. *(Roadmap I, security.)*
2. **More agent presets.** Mirror the existing ones in `devteam/presets.py`
   (e.g. `frontend-deepseek`, a cheap reviewer variant). Update `tests/test_presets.py`.
   *(Presets / model tiering.)*
3. **Extract a shared `e2e.md` skill.** The agent-browser E2E loop currently lives
   only in `skills/qa.md`; extract it to `skills/e2e.md` and map it to both `qa`
   and `frontend` in `skillpack.ROLE_SKILLS`. *(Roadmap C.)*
4. **`doctor` ping for OpenRouter.** Add an optional, non-failing check in
   `devteam/doctor.py` that the OpenCode/OpenRouter key actually resolves a model
   list. *(Reliability.)*

## Medium (1–3 days) — a real feature slice

5. **Deferred-task backoff.** A deferred project is re-attempted every daemon tick
   (~60s) even though the brain cooldown is 1h. Make `daemon.py` skip a project
   whose only viable route is a brain still in `cooldown_until`, until it expires.
   *(Robustness; see `05-EXECUTION-POLICY.md` "known limitations".)*
6. **Real free→cheap escalation.** Today `free_tier_exhausted` is never set true.
   Track free OpenCode call volume in `subscription.py` and pass
   `free_tier_exhausted=True` to `router.route()` once a threshold is hit, so the
   documented escalation actually fires. *(Execution-policy correctness.)*
7. **Grow `devteam bench`.** Extend `devteam/bench.py`: run the produced tests and
   capture pass counts (not just gate pass/fail), add `--repeat N` to average
   cost/latency, and a markdown export. *(Roadmap H; unblocks the jcode decision.)*
8. **QA API smoke runner.** Flesh out the skeleton in `devteam/qa.py`: start the
   built app and hit each `api-contract.md` endpoint (happy + error), returning a
   structured pass/fail per endpoint. *(Roadmap C.)*

## Meaty / roadmap (IDA specialties) — propose a design first

9. **A — intra-project parallelism.** Have pm/architect emit a task DAG;
   independent tasks run concurrently in separate worktrees with a join/merge
   coordinator. Touches `roles.py`, `pipeline.py`, `worktree.py`. *(Roadmap A — the
   biggest throughput multiplier.)*
10. **C — deterministic E2E harness.** A Playwright/agent-browser harness the QA
    agent scripts and runs, with screenshots and a structured report. *(Roadmap C.)*
11. **D — real autonomous deploy.** A Linux deploy target with Caddy + automatic
    SSL, Postgres-per-project, backups, blue-green + rollback, post-deploy smoke.
    Build out `devteam/deploy.py`. *(Roadmap D.)*
12. **E — observability dashboard.** A web view over the event log + scorecard +
    budget. Quick slice: an HTML export of `devteam panel`; full version: a small
    web app reading `eventlog`/`reflective`. *(Roadmap E.)*
13. **G — semantic memory / RAG on Obsidian.** Vector store over past projects,
    decisions and the catalog so agents retrieve "how did we solve X before".
    Greenlit on Obsidian. *(Roadmap G.)*
14. **I — agent sandboxing.** Run each brain in a constrained subprocess/jail with
    least privilege; supply-chain (OSV) + SAST checks on generated deps/code.
    *(Roadmap I — internal safety as parallelism scales.)*

---
**Conventions:** branch `task/<slug>` or `feat/<slug>`, conventional commits, one
intention per PR, English, tests green. See `CONTRIBUTING.md`.
