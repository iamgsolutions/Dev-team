# Extending the system — skills, roles, presets, MCPs

> How to make the team smarter and add new kinds of workers. Everything here is
> additive and test-covered; follow the same patterns and keep `pytest` green.

## 1. Add a SKILL (craft knowledge injected into agents)

A skill is a Markdown file of senior craft that gets injected into an agent's
prompt as the "ROLE KNOWLEDGE" block.

1. Create `devteam/skills/<name>.md` — checklists, anti-patterns, mandatory
   formats. Keep it compact (the loader caps total pack size at ~9 KB). English.
2. Wire it to roles in `devteam/skillpack.py` → `ROLE_SKILLS`:
   ```python
   "backend": ["backend", "python", "testing", "security", "database", "<name>"],
   ```
3. (Optional) Make it conditional on project type in `PROJECT_TYPE_SKILLS`
   (`web` / `api` / `mobile`).
4. `pytest tests/test_skillpack.py`.

**Learning loop:** `devteam learn --role backend "lesson"` appends to
`skills/backend-lessons.md`, which is auto-injected from then on. Use it to turn
recurring failures into permanent craft.

## 2. Add a ROLE / pipeline phase

1. Add the state to `config.STATES` and wire `config.TRANSITIONS` (and
   `HUMAN_CHECKPOINTS` if it needs human approval).
2. Add a task generator in `devteam/roles.py` returning a `PhaseTask`
   (task text + acceptance_criteria + criticality + gates/forbidden) and
   register it in `PHASE_TASKS`.
3. Add its skill mapping in `skillpack.ROLE_SKILLS`.
4. Add the state to `daemon.ACTIONABLE_STATES` if the daemon should run it.
5. Tests in `tests/test_pipeline.py` / `test_deploy_phase.py` as a template.

## 3. Add an AGENT PRESET (swap-the-model worker)

A preset is a named, pinned configuration: role + brain + model + skills + MCPs.
This is how you create "an auditor where you only change the model", etc.

In `devteam/presets.py` add to `BUILTIN`:
```python
"auditor-qwen": AgentPreset(
    "auditor-qwen", role="review", brain=config.BRAIN_OPENCODE,
    model="openrouter/qwen/qwen-2.5-coder-32b-instruct",
    mcps=["filesystem"], notes="Cheap auditor variant."),
```
`devteam presets` lists them. A preset carries its role's full skill pack via
`preset.skills(project_type)`. Use presets to benchmark models on the same role,
or to give a partner team a standard set of agents.

## 4. Add an MCP server (tools for the agents)

The coding CLIs (Claude Code, Codex, OpenCode) all support MCP. A preset
declares the MCPs an agent needs (`mcps=[...]`); the engine passes the working
directory and the CLI loads its MCP config.

To make an MCP available:
1. Configure it in the brain CLI's MCP config (e.g. `claude mcp add <name> ...`,
   or OpenCode's MCP config), so the headless invocation can reach it.
2. Declare it in the relevant presets' `mcps` list (documentation + future
   auto-wiring).

### Standard MCP set (the team's default toolbelt)

These are the MCPs we standardize on, and which roles declare them. Configure
them once per machine in each brain CLI; presets reference them by name.

| MCP | Purpose | Roles that use it |
|---|---|---|
| `filesystem` | scoped file read/write in the worktree | all |
| `github` | repos, branches, PRs, issues | architect, deploy, review |
| `postgres` | inspect schema, run queries against the project DB | backend, qa |
| `agent-browser` | **agent-driven E2E** — `snapshot` (a11y tree + refs) → `click`/`type` → assert; Core Web Vitals; request mocking | qa, frontend |
| `playwright` | scripted browser E2E (when you want deterministic scripts) | qa, frontend |
| `docker` | build/run containers, compose | deploy |
| `fetch` / `web` | read docs/specs/URLs the brief points to | pm, architect |

> **agent-browser vs playwright:** `agent-browser` (Vercel Labs, Apache-2.0) is a
> Rust CLI built for AI agents — the agent gets an accessibility-tree snapshot
> with element refs and clicks/types by ref, instead of writing brittle CSS
> selectors. It's the preferred driver for the QA agent's "see and touch it like
> a user" loop (the browser control costs no tokens; only the agent's reasoning
> does). Install: `npm i -g agent-browser && agent-browser install`. See the QA
> skill (`skills/qa.md`) for the loop. Playwright stays available for scripted,
> fully-deterministic suites.

Project-specific MCPs (Stripe, a vendor API, etc.) are added per project on top
of this base. Keep the set small and least-privilege: an agent should only get
the tools its role needs.

## 5. Add a BRAIN (a new model provider)

1. Create `devteam/brains/<brain>.py` with `invoke(prompt, cwd, timeout_s, model)`
   returning a `BrainResult` (headless CLI, prompt via STDIN, timeout, cost
   estimate). Mirror `gemini.py`.
2. Register it in `brains/__init__.py` `get_invoker`, add the constant in
   `config.py`, add pricing, and (if subscription-backed) add it to
   `subscription.GUARDED_BRAINS` + a daily ration.
3. Wire routing in `router.py` (when it should be chosen).
4. Tests.

**Worked example:** `devteam/brains/jcode.py` is a complete, tested brain added
this way (multi-provider Rust harness) — with one deliberate exception: it does
step 1, 2 and 4 but **not step 3**. jcode is intentionally left *off-route* (the
router never selects it) until the roadmap-H benchmark; reach it only via its
presets. See `docs/jcode.md`. Routing for a normal new brain still belongs in
`router.py`.

## 6. Golden rules for contributors
- The engine is deterministic on purpose. Put intelligence in prompts/skills,
  not in the orchestration code. Orchestration must be predictable and tested.
- Every state write goes through `storage.atomic_write_json`. Every outbound
  message is secret-redacted. Every subprocess has a timeout.
- Keep `pytest` green; add a test for every behavior. English everywhere.
- Never hardcode secrets, IPs or operator paths in the engine; use env vars
  (`config.py` reads them with sane defaults).
