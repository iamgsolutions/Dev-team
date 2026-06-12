# hermes-dev-team — Motor del equipo de desarrollo 24/7

Motor de orquestación del equipo de programadores IA de MG Solutions. Hermes dirige (Discord); este motor ejecuta: máquina de estados por proyecto, routing de cerebros por coste/criticidad, presupuesto con freno duro, invocación de coding agents (Claude Code / Codex / OpenCode) en worktrees aislados, y protocolo de relevo de memoria obligatorio.

**Diseño y contexto:** repo `iamgsolutions/memoria-desarrollo-hermes`, carpeta `build/` (en especial `09-implementation-plan.md`). El estado del build vive en `build/PROGRESS.md`.

## Estructura

- `devteam/` — el paquete. Núcleo: `state` (estados), `budget` (gasto), `instruction` (4 bloques), `router` (qué cerebro), `brains/` (invocadores CLI), `worktree`, `memory` (relevo), `intake` (alta de proyecto), `discord_bridge` (reportes vía `hermes send`), `cli`.
- `tests/` — pytest del núcleo.
- `data/` — estado runtime (no se commitea).

## Uso (CLI)

```
devteam new-project <ruta-al-brief.md> [--name X] [--cap 30]
devteam status [nombre]
devteam pause <nombre> | resume <nombre>
devteam run-task <nombre> --role backend --task "..." (prueba manual de una tarea)
devteam daemon            (bucle 24/7 — Fase 2)
```

## Desarrollo

```
uv venv && uv pip install -e .[dev]
.venv\Scripts\pytest
```

Convenciones: código/commits en inglés, docs en español (regla R7 del spec). Python 3.11.
