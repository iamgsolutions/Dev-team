"""Team roles (S7) - phase task generators for the sequential pipeline.

M4 v1 design (deliberate): each phase runs ONE well-instructed macro-task.
Fine-grained task decomposition (PM plan -> N tasks) is iteration 2 - building
levels honestly instead of faking granularity (build/03 'realistic phasing').

Each role returns the kwargs for executor.execute_task(). Role-specific rules
complement the universal ones (build/05-agent-rules.md).
"""
from __future__ import annotations

from dataclasses import dataclass

from .state import Project


@dataclass
class PhaseTask:
    role: str
    task: str
    acceptance_criteria: list[str]
    expected_output: str
    critical: bool = False
    gates: list[str] | None = None
    forbidden: list[str] | None = None


# Universal norms every role carries; each role ADDS its own lane on top. Kept in
# roles.py (not hidden in the executor default) so the per-role harness is explicit.
UNIVERSAL_FORBIDDEN = [
    "touching the system configuration, other projects, or the engine itself",
    "writing secrets/keys/tokens into code, commits or logs (use env vars)",
    "going outside the scope of THIS task",
]


def _forbidden(*role_specific: str) -> list[str]:
    """Compose a role's forbidden list: the universal norms + this role's lane."""
    return [*UNIVERSAL_FORBIDDEN, *role_specific]


def pm_task(project: Project) -> PhaseTask:
    return PhaseTask(
        role="pm",
        task=(
            "As Product Manager: read ./BRIEF.md and produce the project PRD in ./docs/PRD.md "
            "(create the docs/ folder if it does not exist). The PRD must contain: objective, users, "
            "user stories with MoSCoW priority, verifiable acceptance criteria per "
            "feature, excluded scope, and a high-level technical phase plan. "
            "Do NOT invent requirements: whatever is not in the brief and is critical, list it in a "
            "final section 'Questions for the human'. Documentation in English."
        ),
        acceptance_criteria=[
            "./docs/PRD.md exists with all requested sections",
            "every M feature has verifiable acceptance criteria",
            "critical doubts are in 'Questions for the human' (not assumed)",
        ],
        expected_output="./docs/PRD.md",
        critical=True,  # design quality drives everything downstream
        forbidden=_forbidden(
            "inventing requirements not in the brief (put doubts in 'Questions for the human')",
            "choosing the tech stack or writing code (that is the Architect's job)",
        ),
    )


def architect_task(project: Project) -> PhaseTask:
    from . import catalog
    comps = catalog.all_components()
    catalog_ctx = ""
    if comps:
        catalog_ctx = ("\n\n=== CATALOG OF THE TEAM'S REUSABLE COMPONENTS ===\n"
                       + catalog.format_report()
                       + "\nReuse whatever applies to this project before designing anything new.")
    return PhaseTask(
        role="architect",
        task=(
            "As Architect: read ./docs/PRD.md and ./docs/STANDARDS.md (the team's "
            "standards: structure, code rules, security, tests — they are MANDATORY, "
            "do not invent another organization). If the system has passed you a CATALOG of "
            "reusable components in the context, REUSE whatever applies (do not "
            "rebuild auth, payments, dashboards if they already exist) and note it in docs/architecture.md "
            "('reused components'). Decide the architecture with best practices. "
            "Produce: ./docs/architecture.md (chosen stack and why, folder structure, "
            "ADR-style decisions), ./docs/api-contract.md (ALL endpoints: route, method, "
            "request/response JSON, error codes) and ./docs/data-model.md (entities, fields, "
            "relationships, initial migration). Team default stack: backend Python/FastAPI "
            "or Node/TypeScript (pick the one that fits best and justify it), frontend Next.js+React+TS, "
            "Postgres database. Documentation in English; code identifiers in English."
            + catalog_ctx
        ),
        acceptance_criteria=[
            "architecture.md, api-contract.md and data-model.md exist in ./docs/",
            "the API contract covers all M features of the PRD",
            "every stack decision has a justification",
        ],
        expected_output="./docs/architecture.md + api-contract.md + data-model.md",
        critical=True,
        forbidden=_forbidden(
            "writing implementation code (you design CONTRACTS, not code)",
            "deviating from docs/STANDARDS.md (it overrides your taste)",
        ),
    )


def backend_task(project: Project) -> PhaseTask:
    return PhaseTask(
        role="backend",
        task=(
            "As Backend Engineer: implement EXACTLY ./docs/api-contract.md following "
            "./docs/architecture.md, ./docs/data-model.md and the standards in ./docs/STANDARDS.md "
            "(structure, error handling, security, tests). Include: complete API code, "
            "input validation, error handling with the contract's codes, and tests "
            "(unit + integration) for each endpoint including error cases. If the contract "
            "has a problem, do NOT change it: document the objection in NOTES.md and continue "
            "implementing what was contracted. Code and commits in English."
        ),
        acceptance_criteria=[
            "all contract endpoints implemented",
            "tests for each endpoint (success + error) included",
            "the project starts without errors and the tests pass locally",
        ],
        expected_output="backend code + tests, per the architecture.md structure",
        gates=["lint", "tests"],
        forbidden=_forbidden(
            "changing the API contract — if it's wrong, note it in NOTES.md and implement as contracted",
            "implementing the frontend (stay in the backend)",
        ),
    )


def frontend_task(project: Project) -> PhaseTask:
    return PhaseTask(
        role="frontend",
        task=(
            "As Frontend Engineer: implement the interface per ./docs/PRD.md (user "
            "flows) consuming EXACTLY ./docs/api-contract.md, with the structure and "
            "rules of ./docs/STANDARDS.md. Read NOTES.md: the backend "
            "left warnings there about the real response formats. Include loading and "
            "error states on every API call. Code and commits in English."
        ),
        acceptance_criteria=[
            "all M flows of the PRD are completable from the UI",
            "every API call handles success, loading and error",
            "the frontend build passes without errors",
        ],
        expected_output="frontend application per architecture.md",
        gates=["lint", "build"],
        forbidden=_forbidden(
            "changing the API contract — consume it EXACTLY as written",
            "modifying backend code (stay in the frontend)",
        ),
    )


def qa_task(project: Project) -> PhaseTask:
    return PhaseTask(
        role="qa",
        task=(
            "As a real QA/Tester: verify the entire project. (1) Run the existing test "
            "suite. (2) Check that EVERY endpoint in ./docs/api-contract.md responds per "
            "contract (success and errors). (3) Check that the PRD user flows work "
            "end to end (front consumes back correctly). Produce ./docs/qa-report.md "
            "with: what you tested, what happened, and an actionable list of defects (how to reproduce, "
            "severity). Be skeptical: your job is to FIND problems. Do NOT fix code: "
            "just report."
        ),
        acceptance_criteria=[
            "./docs/qa-report.md exists with results per endpoint and per flow",
            "each defect has reproduction and severity",
            "final verdict: PASS or FAIL with reasons",
        ],
        expected_output="./docs/qa-report.md",
        forbidden=_forbidden("modifying application code (you only test and report)"),
    )


def review_task(project: Project, author_brain: str | None = None) -> PhaseTask:
    return PhaseTask(
        role="review",
        task=(
            "As Code Reviewer/Auditor: audit the project's code (quality, security, "
            "maintainability). Look for: hardcoded secrets, unvalidated inputs, "
            "SQL/XSS injection, logic errors, API contract deviations. Produce "
            "./docs/review-report.md with classified findings (critical/major/minor) and "
            "an APPROVED or REJECTED verdict (reject if there are critical ones)."
        ),
        acceptance_criteria=[
            "./docs/review-report.md exists with classified findings",
            "justified verdict",
        ],
        expected_output="./docs/review-report.md",
        forbidden=_forbidden("modifying code (you only audit and report)"),
    )


def deploy_task(project: Project) -> PhaseTask:
    return PhaseTask(
        role="deploy",
        task=(
            "As DevOps Engineer: produce the project's deployment ARTIFACTS "
            "following ./docs/STANDARDS.md and the architecture. Generate: a multi-stage "
            "Dockerfile (minimal runtime image, non-root user), docker-compose.yml "
            "(app + its own Postgres + isolated network + healthchecks), a complete "
            ".env.example, a healthcheck endpoint/script, migrations applied at "
            "startup, and ./docs/DEPLOY_RUNBOOK.md (deploy steps + rollback + smoke "
            "test). Do NOT run the deployment (the operator does that); produce and validate "
            "the artifacts (that `docker compose config` is valid). Documentation in "
            "English; standard config files."
        ),
        acceptance_criteria=[
            "Dockerfile, docker-compose.yml and .env.example exist, consistent with the stack",
            "docker compose config is valid (correct syntax)",
            "./docs/DEPLOY_RUNBOOK.md exists with deploy + rollback + smoke test",
            "no hardcoded secret in the artifacts",
        ],
        expected_output="Dockerfile + docker-compose.yml + .env.example + docs/DEPLOY_RUNBOOK.md",
        gates=["build"],
        forbidden=_forbidden(
            "running the actual deployment (you produce + validate artifacts; the operator deploys)",
            "hardcoding secrets into the Dockerfile/compose (use .env.example)",
        ),
    )


# phase (state) -> task generator
PHASE_TASKS = {
    "pm": pm_task,
    "architect": architect_task,
    "backend": backend_task,
    "frontend": frontend_task,
    "qa": qa_task,
    "deploy": deploy_task,
}
