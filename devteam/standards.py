"""Engineering standards (the team's single way of building).

One canonical standard injected into every project as docs/STANDARDS.md.
The Architect MUST follow it instead of inventing structure per project -
this is what makes 10 projects feel built by one team (human's mandate:
"mismo criterio, mismo lenguaje y formas de organizar el código siempre").

Distilled from senior practice (Fable mentorship session, 2026-06-12).
"""
from __future__ import annotations

STANDARDS_MD = """\
# STANDARDS.md - Estándares de ingeniería del equipo (NO negociables)

Todo proyecto de este equipo se construye igual. El Architect aplica esto;
los demás roles lo siguen. Desviarse requiere anotarlo en docs/architecture.md
con justificación explícita.

## 1. Estructura de proyecto

### Backend Python (FastAPI) - por defecto
```
app/
  main.py            # create_app() + wiring, NADA de lógica
  api/               # routers por recurso (notes.py, users.py)
  core/              # config (pydantic-settings desde env), seguridad
  models/            # SQLAlchemy/SQLModel
  schemas/           # pydantic request/response (NUNCA exponer models crudos)
  services/          # lógica de negocio (los routers NO contienen lógica)
  db.py              # engine/session
migrations/          # alembic
tests/
  conftest.py        # app de test + DB efímera
  test_api_*.py      # un archivo por router
.env.example         # TODAS las vars documentadas, valores fake
Dockerfile
```

### Backend Node/TypeScript (si el proyecto lo exige)
```
src/
  index.ts           # bootstrap, NADA de lógica
  routes/  services/  models/  schemas/  config.ts
tests/
```

### Frontend Next.js + TypeScript
```
src/
  app/               # app router; páginas = composición, no lógica
  components/        # ui/ (genéricos) y features/ (por dominio)
  lib/api.ts         # ÚNICO punto de llamadas al backend (fetch wrapper)
  lib/types.ts       # tipos compartidos del contrato API
```
Toda llamada a API pasa por lib/api.ts y maneja: éxito, carga, error.

## 2. Reglas de código
- Idioma: código/identificadores/commits INGLÉS; docs y comentarios de
  negocio ESPAÑOL.
- Nombres: descriptivos, sin abreviar (getUserNotes, no getUN).
- Funciones cortas (<40 líneas); módulos cortos (<400 líneas).
- Tipado SIEMPRE: type hints en Python, strict TypeScript.
- Errores: NUNCA tragarse excepciones. Capturar -> log con contexto ->
  respuesta de error del contrato. Backend responde {"detail": "..."}
  con códigos HTTP correctos (400 input, 401/403 auth, 404, 409, 422, 500).
- Validación de TODO input externo (pydantic/zod) ANTES de tocar lógica.
- Sin código muerto, sin TODOs sin issue, sin console.log/print en main.

## 3. Seguridad (mínimo SIEMPRE, sin excepción)
- Secretos SOLO en .env (en .gitignore). .env.example documenta sin valores.
- SQL siempre parametrizado (ORM); NUNCA f-strings/concatenación en queries.
- Passwords: bcrypt/argon2. Tokens: JWT con expiración. CORS explícito.
- Inputs sanitizados; salidas escapadas (XSS); uploads validados.
- Dependencias: versiones fijadas (lockfile committeado).

## 4. Tests (definition of done incluye esto)
- Cada endpoint: test de éxito + tests de errores (validación, no-existe).
- Lógica de negocio (services/): tests unitarios.
- Mínimo orientativo: 70% coverage en services/ y api/.
- Tests deterministas: sin red externa, sin sleeps, DB efímera.

## 5. Git
- Commits convencionales: feat:/fix:/test:/docs:/chore:/refactor:.
- Mensajes en inglés, imperativo, <72 chars la primera línea.

## 6. Documentación mínima por proyecto
- README.md: qué es, cómo arrancar (3 comandos máx), cómo testear.
- docs/architecture.md, docs/api-contract.md, docs/data-model.md (Architect).
- .env.example completo.
"""


def write_standards(project_path) -> None:
    from pathlib import Path
    docs = Path(project_path) / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "STANDARDS.md").write_text(STANDARDS_MD, encoding="utf-8")
