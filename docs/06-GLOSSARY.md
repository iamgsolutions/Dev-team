# Glossary & code map

Two tables: the **vocabulary** the project uses everywhere, and a **concept →
file → test** index so you can jump straight to the code (and the test that pins
its behavior) for any feature.

## Vocabulary

| Term | What it means here |
|---|---|
| **Brain** | A coding model behind a headless CLI (Claude Code, Codex, OpenCode, Gemini, jcode). The thing that actually reads/writes code. |
| **Director** | Hermes — the high-level agent that runs the engine, talks to the human, approves nothing on its own. Not a brain that writes code. |
| **Engine (`devteam`)** | Deterministic Python that enforces process: routing, budget, gates, audit, memory, state. "AI decides content; the engine enforces process." |
| **Role** | A pipeline function: pm, architect, backend, frontend, qa, review, deploy. Determines the skill pack and the task. |
| **Skill** | A markdown craft file (`skills/*.md`) injected into an agent's prompt as ROLE KNOWLEDGE — senior checklists/anti-patterns. |
| **Preset** | A named, pinned worker config (role + brain + model + MCPs). Swap the model to get a new worker. |
| **MCP** | A tool server a brain can call (filesystem, github, postgres, playwright, agent-browser…). Declared per preset. |
| **5-block instruction** | Every brain call = ORIENTATION + TASK + CONSTRAINTS + (optional ROLE KNOWLEDGE) + CLOSE-OUT. Missing a mandatory block = the build raises. |
| **Memory handoff** | Stateless agents, stateful repo: an agent reads `STATE.md`/`NOTES.md` first and MUST update them before finishing. Verified by mtime; a no-op re-invoke warns. |
| **Checkpoint** | A human approval gate. After pm (PRD) and architect (architecture), and a final acceptance after review. |
| **Gate** | A hard pre-merge check (`run_gates`): always-on secrets scan + lint/tests/build. A gate that runs and fails blocks the merge. |
| **Audit** | A multi-model review of a diff before merge (`audit_worktree`), criticality-scaled. A listed `critical` finding forces a REJECT. |
| **Criticality / `critical`** | A per-task flag (pm/architect and auth/payments/data work) that escalates to a premium brain and a 3-auditor panel. |
| **Ration** | Daily call budget for a guarded (premium) brain. claude 15 / codex 20 / gemini 0 by default. |
| **Cooldown** | After a rate-limit, a premium brain rests for 1h (`DEFAULT_COOLDOWN_S`). |
| **Deferred** | A task that didn't run because premium is resting/exhausted. Not an error; retried on a later daemon tick. |
| **Scorecard / bench** | Per-model success/failure tally (`reflective.py`). A sustained-failure model is *benched* (excluded from fallback); premium brains are protected. |
| **Catalog / SAA** | The reusable-component library (auth, payments, dashboards…). The architect reuses from it before building; the Solution Architect Agent assembles solutions from it. |
| **Worktree** | An isolated git worktree + branch per task, so parallel/retried work never collides on the main checkout. |
| **Daemon** | The 24/7 loop that ticks projects forward, applies Discord interventions, and runs the auto-bench sweep. |
| **Doctor** | A no-token health check of every connection the team depends on. |
| **Event log** | An append-only, secret-redacted JSONL flight recorder of what happened (`devteam log`). |

## Concept → file → test

| Concept | Primary file | Key function(s) | Test |
|---|---|---|---|
| Task spine (route→instruct→worktree→invoke→verify→charge→commit) | `devteam/executor.py` | `execute_task` | `tests/test_cascade.py`, `test_pipeline.py` |
| Pipeline / phases / checkpoints | `devteam/pipeline.py` | `run_phase`, `approve` | `tests/test_pipeline.py` |
| Brain routing (which brain/model) | `devteam/router.py` | `route`, `fallback_chain` | `tests/test_router.py` |
| Brains (headless CLIs) | `devteam/brains/*.py` | `invoke`, `get_invoker` | `tests/test_brains.py` |
| 5-block instruction | `devteam/instruction.py` | `Instruction.build` | `tests/test_instruction.py` |
| Skill packs | `devteam/skillpack.py` | `load_for_role` | `tests/test_skillpack.py` |
| Memory handoff | `devteam/memory.py` | `snapshot_memory`, `verify_handoff` | `tests/test_memory.py` |
| Quality gates + secrets scan | `devteam/gates.py` | `run_gates`, `scan_secrets` | `tests/test_gates.py`, `test_audit.py` |
| Multi-model audit | `devteam/audit.py` | `audit_worktree`, `_parse_verdict` | `tests/test_audit.py` |
| Subscription guardian (rations) | `devteam/subscription.py` | `available`, `report_rate_limit` | `tests/test_subscription.py` |
| Budget cap/alert/pause | `devteam/budget.py` | `charge`, `remaining` | `tests/test_budget.py` |
| Scorecard + auto-bench | `devteam/reflective.py` | `record`, `auto_bench` | `tests/test_reflective.py` |
| Model/brain benchmark (roadmap H) | `devteam/bench.py` | `run_bench`, `format_report` | `tests/test_bench.py` |
| Project state machine | `devteam/state.py` | `Project`, `transition` | `tests/test_state.py` |
| Intake (brief → project) | `devteam/intake.py` | `new_project`, `validate_brief` | `tests/test_intake.py` |
| Adopt an existing repo | `devteam/adopt.py` | `adopt_project` | `tests/test_adopt.py` |
| Reusable-component catalog | `devteam/catalog.py` | `register`, `search` | `tests/test_catalog.py` |
| Agent presets | `devteam/presets.py` | `get`, `by_role` | `tests/test_presets.py` |
| Discord intervention listener | `devteam/discord_listener.py` | `parse_command`, `check_interventions` | `tests/test_listener.py` |
| Atomic storage + secret redaction | `devteam/storage.py` | `atomic_write_json`, `redact` | `tests/test_storage.py` |
| Event log | `devteam/eventlog.py` | `record`, `format_tail` | `tests/test_eventlog.py` |
| 24/7 daemon | `devteam/daemon.py` | `tick`, `loop` | `tests/test_daemon.py` |
| Deploy phase | `devteam/deploy.py` | (phase task) | `tests/test_deploy_phase.py` |
| Health check | `devteam/doctor.py` | `run_doctor` | (run `devteam doctor`) |

Tuning knobs and the full routing matrix: `05-EXECUTION-POLICY.md`.
