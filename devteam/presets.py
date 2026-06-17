"""Agent presets - ready-made agent configurations (role + brain + model +
skills + MCPs + rules) where you only swap the model to get a new worker.

This is the "harness of tools, skills, rules and MCPs" the team can hand to
collaborators: define an auditor / architect / programmer once, then spin up
variants by changing just the model. The router still auto-routes by default;
presets are for when you want a PINNED, named configuration (e.g. for a
benchmark of models on the same role, or a partner team's standard agents).

A preset does not run anything by itself; it produces the (brain, model, skills,
mcps) that the executor/router use. MCPs are declared here and resolved by the
brain CLIs that support them (Claude Code / Codex / OpenCode all read MCP config).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import config


@dataclass
class AgentPreset:
    name: str
    role: str                       # maps to skill pack + pipeline phase
    brain: str                      # claude | codex | gemini | opencode
    model: str | None = None        # explicit model (None = brain default)
    mcps: list[str] = field(default_factory=list)   # MCP servers this agent needs
    notes: str = ""

    def skills(self, project_type: str | None = None) -> str:
        from .skillpack import load_for_role
        return load_for_role(self.role, project_type)


# Built-in presets. Swap `model=` to benchmark a different model on the same role.
# MCPs are advisory: list what the agent benefits from (github, postgres, fs...).
BUILTIN: dict[str, AgentPreset] = {
    # --- Architects (design, premium) ---
    "architect-claude": AgentPreset("architect-claude", "architect", config.BRAIN_CLAUDE,
                                    mcps=["github", "filesystem"],
                                    notes="Primary architect: best design reasoning."),
    "architect-codex": AgentPreset("architect-codex", "architect", config.BRAIN_CODEX,
                                   mcps=["github", "filesystem"],
                                   notes="Alternate architect / second opinion."),

    # --- Programmers (execution, cheap/free) ---
    "backend-free": AgentPreset("backend-free", "backend", config.BRAIN_OPENCODE,
                                model=config.OPENCODE_FREE_MODELS[0],
                                mcps=["filesystem", "postgres"],
                                notes="Default backend worker, free tier."),
    "backend-deepseek": AgentPreset("backend-deepseek", "backend", config.BRAIN_OPENCODE,
                                    model=config.OPENCODE_CHEAP_MODELS[0],
                                    mcps=["filesystem", "postgres"],
                                    notes="Backend worker, cheap-strong tier."),
    "frontend-free": AgentPreset("frontend-free", "frontend", config.BRAIN_OPENCODE,
                                 model=config.OPENCODE_FREE_MODELS[0],
                                 mcps=["filesystem"],
                                 notes="Default frontend worker, free tier."),
    # jcode-based worker: fast/low-RAM Rust harness, multi-provider. Candidate
    # for high-parallelism batches (roadmap A) - benchmark vs opencode (roadmap H)
    # before promoting. Pin a free OpenRouter model via `model=` for cost safety.
    "backend-jcode": AgentPreset("backend-jcode", "backend", config.BRAIN_JCODE,
                                 mcps=["filesystem", "postgres"],
                                 notes="Experimental: jcode workhorse (low-RAM, fast). Pin a free model before use."),

    # --- Auditors (review, diverse brain) ---
    "auditor-gemini": AgentPreset("auditor-gemini", "review", config.BRAIN_GEMINI,
                                  mcps=["filesystem"],
                                  notes="Preferred auditor: diverse + huge context (saves codex ration)."),
    "auditor-codex": AgentPreset("auditor-codex", "review", config.BRAIN_CODEX,
                                 mcps=["filesystem"],
                                 notes="Auditor when author was claude/gemini."),
    "auditor-free": AgentPreset("auditor-free", "review", config.BRAIN_OPENCODE,
                                model=config.OPENCODE_FREE_MODELS[1],
                                mcps=["filesystem"],
                                notes="Free-tier auditor for non-critical work."),

    # --- QA / Tester ---
    "qa-free": AgentPreset("qa-free", "qa", config.BRAIN_OPENCODE,
                           model=config.OPENCODE_FREE_MODELS[0],
                           mcps=["filesystem", "playwright"],
                           notes="Functional tester (API + E2E web)."),

    # --- DevOps ---
    "deploy-free": AgentPreset("deploy-free", "deploy", config.BRAIN_OPENCODE,
                               model=config.OPENCODE_FREE_MODELS[0],
                               mcps=["filesystem", "docker"],
                               notes="Generates deploy artifacts (Dockerfile/compose/runbook)."),
}


def get(name: str) -> AgentPreset | None:
    return BUILTIN.get(name)


def by_role(role: str) -> list[AgentPreset]:
    return [p for p in BUILTIN.values() if p.role == role.lower()]


def all_presets() -> list[AgentPreset]:
    return list(BUILTIN.values())


def format_report() -> str:
    lines = [f"{'PRESET':<20}{'ROLE':<11}{'BRAIN':<10}{'MODEL':<42}MCPs"]
    for p in all_presets():
        lines.append(f"{p.name:<20}{p.role:<11}{p.brain:<10}"
                     f"{(p.model or 'default'):<42}{','.join(p.mcps)}")
    return "\n".join(lines)
