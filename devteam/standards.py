"""Engineering standards (the team's single way of building).

One canonical standard injected into every project as docs/STANDARDS.md.
The Architect MUST follow it instead of inventing structure per project -
this is what makes 10 projects feel built by one team (human's mandate:
"same criteria, same language and ways of organizing the code, always").

Distilled from senior practice (Fable mentorship session, 2026-06-12).
"""
from __future__ import annotations

STANDARDS_MD = """\
# STANDARDS.md - Team engineering standards (NON-negotiable)

Every project on this team is built the same way. The Architect applies this;
the other roles follow it. Deviating requires noting it in docs/architecture.md
with an explicit justification.

## 1. Project structure

### Backend Python (FastAPI) - default
```
app/
  main.py            # create_app() + wiring, NO logic
  api/               # routers per resource (notes.py, users.py)
  core/              # config (pydantic-settings from env), security
  models/            # SQLAlchemy/SQLModel
  schemas/           # pydantic request/response (NEVER expose raw models)
  services/          # business logic (routers do NOT contain logic)
  db.py              # engine/session
migrations/          # alembic
tests/
  conftest.py        # test app + ephemeral DB
  test_api_*.py      # one file per router
.env.example         # ALL vars documented, fake values
Dockerfile
```

### Backend Node/TypeScript (if the project requires it)
```
src/
  index.ts           # bootstrap, NO logic
  routes/  services/  models/  schemas/  config.ts
tests/
```

### Frontend Next.js + TypeScript
```
src/
  app/               # app router; pages = composition, no logic
  components/        # ui/ (generic) and features/ (per domain)
  lib/api.ts         # the ONLY point for backend calls (fetch wrapper)
  lib/types.ts       # shared types from the API contract
```
Every API call goes through lib/api.ts and handles: success, loading, error.

## 2. Code rules
- Language: code/identifiers/commits ENGLISH; docs and business
  comments ENGLISH.
- Names: descriptive, not abbreviated (getUserNotes, not getUN).
- Short functions (<40 lines); short modules (<400 lines).
- ALWAYS typed: type hints in Python, strict TypeScript.
- Errors: NEVER swallow exceptions. Catch -> log with context ->
  the contract's error response. Backend responds {"detail": "..."}
  with correct HTTP codes (400 input, 401/403 auth, 404, 409, 422, 500).
- Validation of ALL external input (pydantic/zod) BEFORE touching logic.
- No dead code, no TODOs without an issue, no console.log/print in main.

## 3. Security (the minimum ALWAYS, no exception)
- Secrets ONLY in .env (in .gitignore). .env.example documents without values.
- SQL always parameterized (ORM); NEVER f-strings/concatenation in queries.
- Passwords: bcrypt/argon2. Tokens: JWT with expiration. Explicit CORS.
- Sanitized inputs; escaped outputs (XSS); validated uploads.
- Dependencies: pinned versions (committed lockfile).

## 4. Tests (definition of done includes this)
- Each endpoint: success test + error tests (validation, not-found).
- Business logic (services/): unit tests.
- Indicative minimum: 70% coverage in services/ and api/.
- Deterministic tests: no external network, no sleeps, ephemeral DB.

## 5. Git
- Conventional commits: feat:/fix:/test:/docs:/chore:/refactor:.
- Messages in English, imperative, <72 chars on the first line.

## 6. Minimum documentation per project
- README.md: what it is, how to start (3 commands max), how to test.
- docs/architecture.md, docs/api-contract.md, docs/data-model.md (Architect).
- complete .env.example.
"""


def write_standards(project_path) -> None:
    from pathlib import Path
    docs = Path(project_path) / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "STANDARDS.md").write_text(STANDARDS_MD, encoding="utf-8")
