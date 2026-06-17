# SKILL: Python — this shop's style (3.11+, FastAPI)

- Type hints on EVERYTHING: signatures, returns, attributes. `mypy` must pass.
- pydantic v2 for schemas; `model_config = ConfigDict(from_attributes=True)`
  to map from the ORM. NEVER return raw ORM models.
- FastAPI dependencies (`Depends`) for the DB session, current user, pagination
  — no globals or hand-rolled singletons.
- Exceptions: define your own `AppError(status, detail)`; a global handler
  translates them into the contract format. `except Exception` only at the edge
  with a log + a generic 500.
- Async where it fits: async endpoints; DB calls with an async driver OR everything
  synchronous — do NOT mix (deadlocks).
- `pathlib` over os.path; f-strings; dataclasses for internal structures.
- Imports: stdlib / third-party / local, separated. No circular imports:
  if one appears, the design is wrong — move it to a shared module.
- Tests: pytest + fixtures (conftest: test app + ephemeral sqlite DB +
  httpx client). `assert` with messages on non-obvious comparisons.
- None of: single-letter variables (except indices), functions >40 lines,
  comments that restate the code, `# type: ignore` without justification.
