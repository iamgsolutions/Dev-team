# SKILL: DevOps / Deploy — de "compila" a "vivo y vendible"

## Tu producto es un despliegue REPRODUCIBLE: cualquiera lo levanta con un comando.

### Artefactos que SIEMPRE produces
- **Dockerfile multi-stage**: stage build (deps + compilación) → stage runtime
  mínimo (imagen slim, usuario no-root, solo el artefacto + deps de producción).
  Nada de secretos en capas; usa ARG/ENV en runtime.
- **docker-compose.yml**: app + su Postgres + (si aplica) Redis, en una red
  propia aislada, con `depends_on` + healthchecks. Volúmenes nombrados para datos.
- **.env.example** completo (todas las vars, valores fake) + carga desde env.
- **Healthcheck**: endpoint `/health` (y `/ready` si hay dependencias) +
  `HEALTHCHECK` en el Dockerfile. Sin esto no se sabe si arrancó.
- **Migraciones en arranque**: el contenedor aplica migraciones antes de servir
  (script de entrypoint idempotente), o un job de migración separado.
- **Reverse proxy + TLS**: Caddy (SSL automático Let's Encrypt) como front;
  subdominio por proyecto. nginx solo si ya existe en el host (NO tocar el ajeno).
- **Smoke test post-deploy**: script que tras levantar pega a `/health` y a 1-2
  endpoints clave; si falla, el deploy se considera fallido.
- **Backups**: cron de `pg_dump` con retención; documenta restore VERIFICADO.

### Reglas
- Idempotencia: re-ejecutar el deploy no rompe nada (no duplica datos, no pierde
  volúmenes). `docker compose up -d` debe converger al estado deseado.
- 12-factor: config por entorno, logs a stdout, procesos sin estado local.
- Nunca `latest` sin fijar; etiqueta imágenes con versión/commit.
- Rollback: documenta cómo volver a la versión anterior (imagen previa + dump).
- Si el host es compartido, NO toques servicios de otros (regla crítica): valida
  con `nginx -t` / `docker compose config` antes de aplicar.

### Definición de hecho
- [ ] `docker compose up` levanta TODO desde cero en una máquina limpia.
- [ ] `/health` responde 200; el smoke test pasa.
- [ ] Migraciones aplican solas; datos persisten al reiniciar.
- [ ] .env.example cubre cada variable; ningún secreto en el repo.
- [ ] Runbook de deploy + rollback en docs/.
