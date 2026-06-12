# SKILL: Python — el estilo de esta casa (3.11+, FastAPI)

- Type hints en TODO: firmas, retornos, atributos. `mypy` debe pasar.
- pydantic v2 para schemas; `model_config = ConfigDict(from_attributes=True)`
  para mapear desde ORM. NUNCA devolver modelos ORM crudos.
- Dependencias FastAPI (`Depends`) para sesión DB, usuario actual, paginación
  — nada de globals ni singletons a mano.
- Excepciones: define `AppError(status, detail)` propias; un handler global
  las traduce al formato del contrato. `except Exception` solo en el borde
  con log + 500 genérico.
- Async donde toque: endpoints async; llamadas a DB con driver async O todo
  síncrono — NO mezclar (deadlocks).
- `pathlib` sobre os.path; f-strings; dataclasses para estructuras internas.
- Imports: stdlib / terceros / locales, separados. Sin imports circulares:
  si aparece uno, el diseño está mal — muévelo a un módulo común.
- Tests: pytest + fixtures (conftest: app de test + DB sqlite efímera +
  cliente httpx). `assert` con mensajes en comparaciones no obvias.
- Nada de: variables de una letra (salvo índices), funciones >40 líneas,
  comentarios que repiten el código, `# type: ignore` sin justificar.
