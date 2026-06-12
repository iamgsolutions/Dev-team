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

# --- Budget defaults (spec R3/R6) -------------------------------------------

DEFAULT_BUDGET_CAP_USD = 30.0   # mid of the 20-50 range chosen by the human
BUDGET_ALERT_RATIO = 0.80       # alert at 80%
MAX_TASK_RETRIES = 3            # per-task retry budget before escalating

# --- Brains and models (spec ADR-012/013, 07-technical-decisions) -----------

BRAIN_CLAUDE = "claude"
BRAIN_CODEX = "codex"
BRAIN_OPENCODE = "opencode"

# Default model per brain. OpenCode free-first cascade lives in router/brains.
DEFAULT_MODELS = {
    BRAIN_CLAUDE: None,  # claude CLI uses its own configured default
    BRAIN_CODEX: None,   # codex CLI uses its own configured default
    BRAIN_OPENCODE: "openrouter/meta-llama/llama-3.3-70b-instruct:free",
}

OPENCODE_FREE_MODELS = [
    "openrouter/meta-llama/llama-3.3-70b-instruct:free",
    "openrouter/nousresearch/hermes-3-llama-3.1-405b:free",
    "openrouter/google/gemma-4-26b-a4b-it:free",
]
OPENCODE_CHEAP_MODELS = [
    "openrouter/deepseek/deepseek-chat",      # strong & cheap
    "openrouter/qwen/qwen-2.5-coder-32b-instruct",
    "openrouter/google/gemini-2.0-flash-001",
]

# USD per 1M tokens (input, output). Approximate, for estimation only.
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # free tier
    "openrouter/meta-llama/llama-3.3-70b-instruct:free": (0.0, 0.0),
    "openrouter/nousresearch/hermes-3-llama-3.1-405b:free": (0.0, 0.0),
    "openrouter/google/gemma-4-26b-a4b-it:free": (0.0, 0.0),
    # cheap tier
    "openrouter/deepseek/deepseek-chat": (0.30, 1.20),
    "openrouter/qwen/qwen-2.5-coder-32b-instruct": (0.20, 0.80),
    "openrouter/google/gemini-2.0-flash-001": (0.10, 0.40),
    # premium (when CLIs don't self-report cost)
    "claude-default": (3.00, 15.00),   # sonnet-class assumption
    "codex-default": (2.00, 8.00),     # gpt-5-class assumption (verify)
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
    "pm": "PRD aprobado por el humano",
    "architect": "Arquitectura aprobada por el humano",
    "review": "Entrega aceptada por el humano",
}


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
