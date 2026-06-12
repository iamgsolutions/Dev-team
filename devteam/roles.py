"""Team roles (S7) - SKELETON for Fase 2 / M4.

Each role = prompt template + default routing + specific rules (05-agent-rules
section 'por rol'). Will provide: role_pm, role_architect, role_backend,
role_frontend, role_qa, role_review.

TODO(M4): implement role prompt builders that produce executor.execute_task()
arguments (task text, acceptance criteria, criticality) from project context.
"""
from __future__ import annotations
