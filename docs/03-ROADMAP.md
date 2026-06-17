# Roadmap — the complex build (toward a Development OS)

> The engine v1 exists and is tested. This is the ambitious work that turns it
> into a system that out-builds a large human team. Each item lists complexity,
> value, and who is well-placed to lead it (IDA = the 35-dev partner team; MG =
> us). These are proposals to discuss and prioritize together.

## A. Parallelism & scale  ★★★ complexity / ★★★ value
The biggest multiplier. Today: one project, sequential phases.
- **Intra-project parallelism**: PM/Architect produce a task DAG; independent
  tasks (e.g. multiple endpoints, backend vs frontend after the contract) run
  concurrently in separate worktrees, with a join/merge coordinator.
- **Multi-project scheduler**: N projects in flight with priority + fair-share
  of the premium rations across them.
- **Distributed workers**: workers on multiple machines pulling from a shared
  task queue (Redis/Postgres-backed), so throughput scales with hardware.
- Lead: **IDA** (queue/coordinator engineering). Foundation already exists
  (worktrees, state machine, isolation).

## B. Smart decomposition  ★★★ / ★★★
Turn a brief into a fine-grained, dependency-aware task graph instead of one
macro-task per phase. The Director becomes a planner. Includes automatic task
sizing per brain (small/literal for free models, complex for premium).
- Lead: MG + IDA jointly (this is the core "intelligence" of the orchestrator).

## C. Real testing infrastructure  ★★★ / ★★★
The QA role runs as an agent today; make it a deterministic harness it can drive:
- API tester: spin up the app, hit every contract endpoint (happy + error),
  assert against the contract automatically.
- E2E web: a Playwright harness the agent scripts and runs, with screenshots
  and a structured report.
- Mobile E2E (React Native / Expo): Detox/Maestro — hard, later.
- Lead: **IDA** (test infrastructure is their strength).

## D. Autonomous deploy (real CD)  ★★ / ★★★
Today the deploy role generates artifacts; make it actually ship:
- A dedicated Linux deploy target (cheap VPS / PaaS), reverse proxy (Caddy)
  with automatic SSL, per-project subdomains, Postgres-per-project, automated
  backups, blue-green + rollback, post-deploy smoke tests.
- Lead: **IDA** (DevOps).

## E. Observability & cost dashboard  ★★ / ★★
A web dashboard (the engine already emits an event log + scorecard + panel):
project board, live cost/budget, model scorecard, event timeline, per-task
token spend. Optionally Langfuse/Helicone for LLM tracing.
- Lead: IDA (frontend) + MG (data model).

## F. Solution Architect Agent — full SAA  ★★★ / ★★★
The catalog exists (register/search). Build the agent that, given a client
brief, assembles a solution from catalog components + builds only the gap, and
learns which compositions work. This is the productization core (ADR-010).
- Lead: MG + IDA.

## G. Semantic memory / RAG  ★★ / ★★
Vector store over past projects, decisions and the catalog so agents retrieve
"how did we solve X before". Today memory is markdown + FTS-style; add embeddings
when project volume justifies it.
- Lead: IDA.

## H. Model evaluation harness  ★★ / ★★
Objectively benchmark models per role (same tasks, compare success/cost/latency)
to drive routing and the auto-bench thresholds with data, not guesses. The
scorecard + presets are the foundation.
- Lead: MG.

## I. Security & sandboxing  ★★★ / ★★★
Agents run shell/code; harden it: run each brain in a container/jail with least
privilege, supply-chain checks on generated deps (OSV), SAST on generated code,
secret-scanning already in gates — extend it. Critical before selling to clients.
- Lead: **IDA** (security engineering).

## J. Human-in-the-loop UX  ★ / ★★
Richer control surface beyond Discord: web approvals, diffs, the ability to
steer mid-project, mobile notifications.
- Lead: IDA (frontend).

## K. Multi-tenant / client isolation  ★★ / ★★★
To sell: per-client isolation (data, secrets, repos, budgets), white-label
deploys, audit trails per tenant. The engine is single-tenant today.
- Lead: MG + IDA.

---

## Suggested first joint targets (highest value / unblocks the rest)
1. **A — intra-project parallelism + task DAG** (B feeds it). The single biggest
   throughput multiplier; turns "fast" into "monstrous".
2. **C — real testing harness.** Quality is what makes the output sellable;
   IDA's strength.
3. **I — sandboxing/security.** Required before any client work.
4. **D — real autonomous deploy.** Closes the loop to "live software".

These four, built in parallel by IDA's specialists while MG drives B/F (the
orchestration intelligence), would take the system from "validated engine" to
"a team that out-builds 20 human developers" within a focused quarter.
