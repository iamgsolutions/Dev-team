# SKILL: DevOps / Deploy — from "it compiles" to "live and sellable"

## Your product is a REPRODUCIBLE deployment: anyone brings it up with one command.

### Artifacts you ALWAYS produce
- **Multi-stage Dockerfile**: build stage (deps + compilation) → minimal runtime
  stage (slim image, non-root user, only the artifact + production deps).
  No secrets in layers; use ARG/ENV at runtime.
- **docker-compose.yml**: app + its Postgres + (if applicable) Redis, on its own
  isolated network, with `depends_on` + healthchecks. Named volumes for data.
- **Complete .env.example** (all vars, fake values) + load from env.
- **Healthcheck**: a `/health` endpoint (and `/ready` if there are dependencies) +
  `HEALTHCHECK` in the Dockerfile. Without this you can't tell if it started.
- **Migrations on startup**: the container applies migrations before serving
  (idempotent entrypoint script), or a separate migration job.
- **Reverse proxy + TLS**: Caddy (automatic Let's Encrypt SSL) as the front;
  a subdomain per project. nginx only if it already exists on the host (do NOT touch someone else's).
- **Post-deploy smoke test**: a script that, after bringing it up, hits `/health` and 1-2
  key endpoints; if it fails, the deploy is considered failed.
- **Backups**: a `pg_dump` cron with retention; document a VERIFIED restore.

### Rules
- Idempotency: re-running the deploy breaks nothing (no duplicated data, no lost
  volumes). `docker compose up -d` must converge to the desired state.
- 12-factor: config per environment, logs to stdout, processes with no local state.
- Never `latest` without pinning; tag images with version/commit.
- Rollback: document how to go back to the previous version (previous image + dump).
- If the host is shared, do NOT touch other people's services (critical rule): validate
  with `nginx -t` / `docker compose config` before applying.

### Definition of done
- [ ] `docker compose up` brings up EVERYTHING from scratch on a clean machine.
- [ ] `/health` responds 200; the smoke test passes.
- [ ] Migrations apply on their own; data persists across restarts.
- [ ] .env.example covers every variable; no secret in the repo.
- [ ] Deploy + rollback runbook in docs/.
