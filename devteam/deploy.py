"""Deployer (S11) - SKELETON for Fase 4 / M6.

Target per spec: Docker (app + own Postgres) + Caddy auto-SSL + subdomain
proyecto.mgsolution.es + automated DB backups.

BLOCKER (2026-06-12): WSL2/Hyper-V impossible on this VPS (no SLAT, nested
virtualization unavailable -> HCS_E_HYPERV_NOT_INSTALLED). Linux containers
cannot run on this Windows host. Options recorded in PROGRESS.md:
  (B) cheap Linux VPS for deploys via SSH (RECOMMENDED - also separates
      orchestrator from generated apps),
  (C) PaaS (Railway/Render/Fly),
  (D) native Windows processes + Caddy windows binary (no containers; staging only).
Human must choose before M6 implementation.

TODO(M6): implement chosen target; deploy(project) -> url; backup schedule.
"""
from __future__ import annotations
