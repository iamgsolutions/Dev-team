"""Deployer (S11) - real deployment of generated projects (roadmap item D).

The `deploy` ROLE (roles.py) already makes agents produce the deploy artifacts
(multi-stage Dockerfile, docker-compose with app + own Postgres, Caddy auto-SSL,
.env.example, healthcheck, DEPLOY_RUNBOOK.md). This module is where the engine
will EXECUTE those artifacts against a real target.

Target (configurable via env, no hardcoded hosts): a Linux deploy host or PaaS,
Caddy reverse proxy with automatic SSL, a subdomain per project, Postgres per
project, automated backups, blue-green + rollback, post-deploy smoke test.

Note: container deployment needs a Linux host; a Windows orchestrator host
should deploy to a separate Linux box/PaaS over SSH (this also isolates the
orchestrator from generated apps - good security practice).

TODO(D): implement deploy(project) -> url against the configured target;
backup schedule; smoke test; rollback.
"""
from __future__ import annotations
