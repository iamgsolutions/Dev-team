"""Global paths, constants and model pricing.

Pricing is a best-effort static table (USD per 1M tokens) used for budget
estimation when a brain does not report its own cost. Refresh periodically
from provider pricing pages / OpenRouter API (TODO: automate in S5 v2).
"""
from __future__ import annotations

import os
from pathlib import Path

# --- Paths -----------------------------------------------------------------

ENGINE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("DEVTEAM_DATA", ENGINE_ROOT / "data"))
PROJECTS_ROOT = Path(os.environ.get("DEVTEAM_PROJECTS", r"C:\Users\Administrator\dev\projects"))

HERMES_EXE = Path(
    os.environ.get(
        "DEVTEAM_HERMES_EXE",
        r"C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\hermes.exe",
    )
)

PROJECT_MEMORY_DIR = ".project-memory"  # inside each project repo

# Known location of npm-installed CLIs (claude/codex/opencode live here as
# .cmd wrappers). subprocess on Windows does not apply PATHEXT, and service
# processes may have a minimal PATH - so we resolve executables explicitly.
NPM_BIN = Path(os.environ.get("APPDATA", r"C:\Users\Administrator\AppData\Roaming")) / "npm"


def resolve_cli(name: str) -> str:
    """Resolve a CLI name to a full executable path (Windows-safe).

    Order: shutil.which (honors PATHEXT) -> NPM_BIN/<name>.cmd|.exe -> name as-is
    (last resort lets the caller surface a clear 'not found' error).
    """
    import shutil

    found = shutil.which(name)
    if found:
        return found
    for suffix in (".cmd", ".exe", ".bat"):
        cand = NPM_BIN / f"{name}{suffix}"
        if cand.exists():
            return str(cand)
    return name

# --- Budget defaults (spec R3/R6) -------------------------------------------

DEFAULT_BUDGET_CAP_USD = 30.0   # mid of the 20-50 range chosen by the human
BUDGET_ALERT_RATIO = 0.80       # alert at 80%
MAX_TASK_RETRIES = 3            # per-task retry budget before escalating

# --- Brains and models (spec ADR-012/013, 07-technical-decisions) -----------

BRAIN_CLAUDE = "claude"
BRAIN_CODEX = "codex"
BRAIN_GEMINI = "gemini"
BRAIN_OPENCODE = "opencode"
BRAIN_JCODE = "jcode"   # fast/low-RAM Rust harness, multi-provider (eval 2026-06)

# Default model per brain. OpenCode free-first cascade lives in router/brains.
# Model IDs verified against `opencode models` output on 2026-06-12.
# NOTE: coding agents need TOOL-USE capable models; the opencode/*-free models
# are curated by the OpenCode gateway for agent work (tool support included).
DEFAULT_MODELS = {
    # Automation uses SONNET, not opus: rations the Max subscription (the
    # humans use it interactively too) while staying premium-grade for design.
    BRAIN_CLAUDE: "sonnet",
    BRAIN_CODEX: None,    # codex CLI uses its own configured default
    BRAIN_GEMINI: None,   # gemini CLI default (Pro subscription limits apply)
    BRAIN_OPENCODE: "opencode/deepseek-v4-flash-free",
    # jcode runs via -p openrouter; None = jcode's own default. Pin a FREE
    # OpenRouter slug per-preset before using it as a workhorse (roadmap H bench).
    BRAIN_JCODE: None,
}

OPENCODE_FREE_MODELS = [
    "opencode/deepseek-v4-flash-free",
    "opencode/north-mini-code-free",
    "opencode/nemotron-3-ultra-free",
]
OPENCODE_CHEAP_MODELS = [
    "openrouter/deepseek/deepseek-v4-flash",
    "openrouter/deepseek/deepseek-chat-v3.1",
    "openrouter/google/gemini-2.5-flash",
]

# USD per 1M tokens (input, output). Approximate, for estimation only.
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # free tier (opencode gateway)
    "opencode/deepseek-v4-flash-free": (0.0, 0.0),
    "opencode/north-mini-code-free": (0.0, 0.0),
    "opencode/nemotron-3-ultra-free": (0.0, 0.0),
    # cheap tier
    "openrouter/deepseek/deepseek-v4-flash": (0.30, 1.20),
    "openrouter/deepseek/deepseek-chat-v3.1": (0.30, 1.20),
    "openrouter/google/gemini-2.5-flash": (0.30, 2.50),
    # premium (when CLIs don't self-report cost)
    "claude-default": (3.00, 15.00),   # sonnet-class assumption
    "codex-default": (2.00, 8.00),     # gpt-5-class assumption (verify)
    "gemini-default": (1.25, 10.00),   # gemini-pro-class assumption
}
FALLBACK_PRICING = (1.0, 3.0)  # unknown model: assume cheap-ish, never free

# --- Project states (spec section 3/R7/R11) ---------------------------------

STATES = [
    "new",
    "clarification",
    "pm",
    "architect",
    "backend",
    "frontend",
    "qa",
    "deploy",
    "review",   # waiting human acceptance (R11 gate)
    "done",
]

# Allowed forward transitions; "paused" is a flag, not a state.
TRANSITIONS: dict[str, list[str]] = {
    "new": ["clarification", "pm"],
    "clarification": ["pm"],
    "pm": ["architect"],          # requires human checkpoint (PRD)
    "architect": ["backend"],     # requires human checkpoint (architecture)
    "backend": ["frontend"],
    "frontend": ["qa"],
    "qa": ["deploy", "backend", "frontend"],  # QA can bounce work back
    "deploy": ["review"],
    "review": ["done", "qa"],     # human may accept or request fixes
    "done": [],
}

# Human checkpoints (spec R3): state -> what must be approved to leave it.
HUMAN_CHECKPOINTS = {
    "pm": "PRD approved by the human",
    "architect": "Architecture approved by the human",
    "review": "Delivery accepted by the human",
}


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
