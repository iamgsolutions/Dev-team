"""Pipeline runner (S6) - SKELETON for Fase 2 / M4.

Will run the strict-sequential pipeline (pm -> architect -> backend -> frontend
-> qa -> deploy -> review) with human checkpoints after pm and architect,
quality gates before merges, and the audit loop. See build/03-build-roadmap.md
FASE 2 and build/06-skills-to-build.md S6/S7.

TODO(M4):
- per-phase task generation from PRD/architecture docs
- human checkpoint wait-loop (Discord approval via intervention listener)
- branch/PR/merge flow using worktree.merge_branch after gates pass
- bounce-back from qa to backend/frontend with corrective tasks
"""
from __future__ import annotations
