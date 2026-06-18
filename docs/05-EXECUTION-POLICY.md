# Execution policy — exactly what runs, when, and at what cost

> This is the single source of truth for **how the system decides which brain and
> model to use for each task at each moment**, how it rations cost, and what
> happens on failure. It reflects the code (`router.py`, `config.py`,
> `subscription.py`, `executor.py`, `audit.py`, `reflective.py`, `budget.py`) —
> not aspiration. Where the code has a known limitation, it is stated honestly.

## The brains (workers)

| Brain | CLI | Role in the team | Cost model |
|---|---|---|---|
| **OpenCode** | `opencode run` | The **workhorse**: all execution (backend/frontend/qa) and free auditors. | Free models first (OpenRouter free tier), then cheap. |
| **Claude Code** | `claude -p` | **Design** (pm/architect) and **critical** work. Premium reasoning. | Rationed (subscription/credit pool). Automation uses **sonnet**, not opus. |
| **Codex** | `codex exec` | Second premium brain (escalation + diverse auditor). | Rationed. |
| **Gemini** | `gemini` | Preferred **auditor** when enabled (diverse + huge context). | Rationed. **Disabled by default** (ration = 0). |
| **jcode** | `jcode run` | Optional fast/low-RAM runner. **Never auto-routed** — opt-in via preset, pending the roadmap-H benchmark. | Whatever provider you pin (pin a free OpenRouter model). |

Default model per brain lives in `config.DEFAULT_MODELS`. Free/cheap OpenCode model
lists live in `config.OPENCODE_FREE_MODELS` / `OPENCODE_CHEAP_MODELS`.

## The routing matrix (what `router.route()` returns)

`executor.execute_task()` calls `route()` with the role, the `critical` flag, the
remaining budget, and live premium availability from the subscription guardian.
The `critical` flag is set per phase in `roles.py` (pm and architect are
`critical=True`).

| Situation | Brain / model chosen | Why |
|---|---|---|
| **Design — pm / architect** (also `critical`) | `claude` (sonnet) **if** budget remaining > `PREMIUM_MIN_BUDGET_USD` ($2) **and** claude ration available | Premium design, few tokens |
| **Execution — backend / frontend / qa** | `opencode` + `OPENCODE_FREE_MODELS[0]` (`deepseek-v4-flash-free`) | Free workhorse |
| **Any CRITICAL task** | Premium escalation chain (below), regardless of role | Critical work earns a premium brain |
| **Budget low** (remaining ≤ $2) on a premium-grade task | `opencode` forced to the best **cheap** model | Protect the budget |

**Premium escalation chain** (for design/critical), in exact order:
1. budget ≤ $2 → OpenCode **cheap** model.
2. claude available → **claude**.
3. else codex available → **codex**.
4. else gemini available → **gemini** (disabled by ration 0 by default → skipped).
5. else → **defer** (the task waits for a later batch; see below).

## Free → cheap → premium cascade (how cheap is actually reached)

Be precise here — the cheap tier is reached in **two real ways**, not via a
"free quota exhausted" signal:

1. **Budget-low branch**: when remaining ≤ $2 on a premium-grade task, the router
   forces the cheap model.
2. **Failure fallback**: when a free OpenCode model **fails**,
   `brains/opencode.invoke_with_fallback()` walks `router.fallback_chain()` —
   all free models, then all cheap models — skipping any **benched** model
   (see Auto-bench). The first `ok` wins.

> Honest note: `route()` has a `free_tier_exhausted` parameter, but the executor
> never sets it true (nothing tracks free-quota consumption). So there is no
> standalone "free exhausted → cheap" trigger; cheap is reached only by the two
> mechanisms above.

## Audit / review policy (authoritative path = `audit.py`)

The live pipeline does **not** route audits through `router.route()`. After
backend/frontend work passes gates, `pipeline.run_phase()` calls
`audit.audit_worktree()`:

- **Normal work** → **1** free OpenCode auditor, a **different** model from the
  author (diversity costs nothing).
- **Critical work** → **2** free auditors **+ 1 premium** (gemini preferred to
  save the codex ration; codex if gemini is resting). **Majority** vote.
- **pm/architect output is not machine-audited** — it passes a **human
  checkpoint** instead.
- **Critical findings are enforced**: an auditor that lists a `critical` finding
  yields a REJECT even if it wrote `APPROVED` (`audit._parse_verdict`). The
  reviewer skills teach the exact parseable format (`VERDICT: APPROVED|REJECTED` +
  `- [critical|major|minor] file:line — …`).

(There is a second, **latent** audit branch inside `router.py` for a `review`/
`audit` role; `PHASE_TASKS` never schedules it, so it is effectively legacy.
`audit.py` governs.)

## Quality gates (before any merge)

Every task's worktree runs `gates.run_gates()` before merge:
- **Secrets gate — always on, non-skippable**: scans the worktree for high-signal
  key patterns (sk-…, ghp_…, AWS, Slack, private keys) across code, config,
  Dockerfiles, etc. A leak fails the gate.
- **Lint / tests / build**: from `.project-memory/gates.json` (written by the
  architect) or inferred from the stack (ruff/pytest, npm scripts).
- A gate that **runs and fails** blocks the merge; a tool that is **not installed**
  is recorded as *skipped*, not silently passed.

## Self-correction cascade (failure handling)

When a phase task fails gates or audit, the agent gets the **exact** failure
feedback and fixes its **own** work in the same worktree, up to
`MAX_TASK_RETRIES` (3). Only after the cascade is exhausted does the project
**pause** and escalate a blocker to Discord. This is the "agents fix their own
mistakes first, escalate only what they can't" rule.

## Rations & cost control (the subscription guardian)

- **Daily call budgets** (`subscription.DEFAULT_DAILY_CALLS`): claude **15**,
  codex **20**, gemini **0** (disabled). OpenCode and jcode are **unguarded**
  (unlimited). Tune with `devteam subs --set claude 10`.
- **GUARDED_BRAINS** = claude, codex, gemini — only these consume rations and
  cooldowns.
- **Rate-limit → cooldown**: when a premium brain reports a usage/rate limit, it
  is rested for **1 hour** (`DEFAULT_COOLDOWN_S = 3600`) and the task **defers**.
  Wake early with `devteam subs --wake claude`.
- **"Deferred"** is **not an error**: the task didn't run because premium is
  resting/exhausted. It does not advance state, does not pause, does not consume a
  retry. The daemon re-attempts it on a later tick.
- **Budget**: per-project cap (default **$30**, `DEFAULT_BUDGET_CAP_USD`); alert
  at **80%** (Discord); at 100% the charge is refused and the project **pauses**.
  Free models cost $0 but are still recorded for volume visibility.

## Auto-bench (model accountability)

`reflective.auto_bench()` (daemon sweep every 20 ticks) benches a model with a
**sustained** failure record: ≥ **8** recorded tasks and a success rate **< 40%**.
Benched models are excluded from the OpenCode fallback chain. **Premium brains
(claude/codex/gemini) are protected** — a rate limit looks like a failure, so a
paid subscription is never benched. Manage manually with
`devteam scorecard --bench <model>` / `--unbench <model>`.

## Where jcode and gemini stand

- **jcode**: registered and callable (`get_invoker`), but `route()` **never
  returns it**. Reach it only via the `backend-jcode` / `auditor-jcode` presets or
  by pinning `brain="jcode"`. Pin a free OpenRouter model first (its default model
  is unset → provider default has no cost guarantee). Benchmark vs OpenCode
  (roadmap H) before promoting. See `jcode.md`.
- **gemini**: fully wired and **code-preferred** as the first auditor — but
  **disabled by a ration of 0**, so it is skipped everywhere until you raise the
  ration (`devteam subs --set gemini 25`), after which it immediately becomes the
  primary auditor and third premium brain.

## Known limitations (be honest with IDA)

1. **Premium hard errors retry the same brain.** A premium `error`/`timeout` (not
   a rate-limit) returns non-ok; the self-heal cascade re-routes and the router
   picks the **same** premium brain again (no cooldown was set), so a
   deterministically-failing brain can consume all 3 attempts before escalating.
   Only `rate_limited` triggers the cross-brain defer. (Improvement tracked.)
2. **Deferred work busy-retries.** A deferred project stays actionable and is
   re-attempted every daemon tick (~60s) even though the cooldown is 1h — harmless
   (no cost, no ration spend on a defer) but noisy; "next batch window" is
   implicit, not scheduled.
3. **Sandboxing is not enforced.** The worktree isolates git state, but an agent
   process can still read/write outside its cwd. This is roadmap item **I**, not a
   solved control.

## How to tune it (operator knobs)

| Want to… | Do |
|---|---|
| Change a daily ration | `devteam subs --set claude 10` |
| Wake a resting brain | `devteam subs --wake claude` |
| Enable Gemini as auditor | `devteam subs --set gemini 25` |
| Bench / unbench a model | `devteam scorecard --bench <model>` / `--unbench <model>` |
| Raise/lower the budget cap | per project (`--cap`) or `config.DEFAULT_BUDGET_CAP_USD` |
| Change premium budget thresholds | `config.PREMIUM_MIN_BUDGET_USD`, `config.AUDIT_PREMIUM_MIN_BUDGET_USD` |
| See the live picture | `devteam panel` (projects, rations, scorecard, health) |
