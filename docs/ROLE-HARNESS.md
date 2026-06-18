# Role harness — what each agent gets to do its job

Every pipeline role is an agent with a tailored **harness**: the craft (skills) it
needs, the tools (MCPs) it can use, the brain tier it runs on, and the norms (its
lane). This is the single view; the pieces live in code:

- **Skills** (craft injected as ROLE KNOWLEDGE): `devteam/skillpack.py` → `ROLE_SKILLS`
  (+ `PROJECT_TYPE_SKILLS` layers web/api/mobile extras). Files: `devteam/skills/*.md`.
- **Tools / MCPs**: `devteam/presets.py` (`mcps=[...]` per preset).
- **Brain tier**: `devteam/router.py` (see `05-EXECUTION-POLICY.md`).
- **Norms** (what it must NOT do): `devteam/roles.py` (`UNIVERSAL_FORBIDDEN` + each
  role's lane) + the universal `AGENTS.md` written into every repo.

## Universal norms (every role carries these)
- Don't touch the system configuration, other projects, or the engine itself.
- Never write secrets/keys/tokens into code, commits or logs — use env vars.
- Stay within the scope of THIS task. Read STATE/NOTES first; update them before finishing.

## The roles

### PM — turns the brief into a PRD
- **Goal:** a verifiable PRD (objective, users, MoSCoW stories, acceptance criteria, open questions).
- **Skills:** pm, product-quality, data-privacy.
- **Tools:** filesystem, fetch (read referenced specs/links).
- **Brain:** premium (Claude) — design quality drives everything downstream.
- **Lane (forbidden):** inventing requirements (ask in "Questions for the human"); choosing the stack or writing code.

### Architect — turns the PRD into contracts
- **Goal:** architecture.md + api-contract.md + data-model.md. **Reuses the catalog** before building.
- **Skills:** architect, security, api-design, database, performance.
- **Tools:** github, filesystem, fetch.
- **Brain:** premium (Claude → Codex).
- **Lane:** writing implementation code (you design CONTRACTS); deviating from STANDARDS.md.

### Backend — implements the contract
- **Goal:** the API exactly per api-contract.md, with validation, error handling and tests.
- **Skills:** backend, python, testing, security, database, observability, git-workflow.
- **Tools:** filesystem, postgres, github.
- **Brain:** free OpenCode (the workhorse); cheap/premium only if it struggles.
- **Lane:** changing the contract (note objections in NOTES.md); touching the frontend.
- **Gates:** lint, tests. **Audited** by a different brain before merge.

### Frontend — builds the UI
- **Goal:** the UI per the PRD flows, consuming the contract exactly, with loading/error/success states.
- **Skills:** frontend, typescript, testing, security, accessibility, performance, **e2e**, git-workflow.
- **Tools:** filesystem, agent-browser (self-verify its own UI).
- **Brain:** free OpenCode.
- **Lane:** changing the contract; modifying backend code.
- **Gates:** lint, build. **Audited** before merge.

### QA — breaks it before the client does
- **Goal:** a qa-report.md: run the suite, hit every endpoint (happy+error), walk every PRD flow E2E.
- **Skills:** qa, **e2e**, testing, debugging, api-design.
- **Tools:** filesystem, agent-browser (drive the UI), fetch (hit APIs), playwright (optional).
- **Brain:** free OpenCode.
- **Lane:** modifying application code — you only test and report.

### Review / Audit — the professional skeptic
- **Goal:** find what the author missed (secrets, injection, contract deviations, logic). Parseable VERDICT.
- **Skills:** review, security, code-style.
- **Tools:** filesystem.
- **Brain:** a brain DIFFERENT from the author (diverse free; +1 premium for critical work). Runs via `audit.py`.
- **Lane:** modifying code — you only audit and report. A **critical** finding forces REJECTED (engine-enforced).

### Deploy — produces shippable artifacts
- **Goal:** Dockerfile + docker-compose + .env.example + DEPLOY_RUNBOOK.md, validated (`docker compose config`).
- **Skills:** devops, observability, security, git-workflow.
- **Tools:** filesystem, docker, github.
- **Brain:** free OpenCode.
- **Lane:** running the actual deployment (the operator does that); hardcoding secrets (use .env.example).
- **Gates:** build.

## Project-type layers (added on top of the role pack)
`PROJECT_TYPE_SKILLS` adds extra craft so the pack is always pertinent:
- **web** → frontend +accessibility/performance; architect +performance.
- **api** → backend +api-design/performance/observability; architect +api-design/performance.
- **mobile** → frontend/architect +performance.

## Extending a role's harness
- Add craft → write `skills/<name>.md` and map it in `skillpack.ROLE_SKILLS` (a test
  asserts every mapped skill resolves to a file). See `02-EXTENDING.md`.
- Add a tool → declare the MCP in the role's preset `mcps=[...]`; configure it in the
  brain CLI. Standard set in `02-EXTENDING.md`.
- Tighten a norm → edit the role's `forbidden=_forbidden(...)` in `roles.py`.
