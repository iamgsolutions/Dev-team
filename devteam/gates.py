"""Quality gates (S8) - SKELETON for Fase 3 / M5.

Hard gate before any merge: lint + typecheck + build + tests must pass
(ruff/mypy/pytest for Python; eslint/tsc/vitest for TS - see
build/07-technical-decisions.md).

TODO(M5): detect project stack, run the right toolchain inside the worktree,
return structured pass/fail with failure details as corrective tasks.
"""
from __future__ import annotations
