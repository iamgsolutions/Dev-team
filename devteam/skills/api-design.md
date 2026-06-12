# SKILL: Diseño de APIs — convenciones del equipo (REST)

- Rutas: sustantivos en plural, kebab-case: `/notes`, `/user-profiles/{id}`.
  Nada de verbos en rutas (`/getNotes` ❌). Anidar máximo 1 nivel.
- Métodos: GET lee (sin efectos), POST crea (201 + objeto creado), PUT/PATCH
  actualiza (200 + objeto), DELETE borra (204 sin cuerpo).
- Códigos: 400 input inválido · 401 sin autenticar · 403 sin permiso ·
  404 no existe · 409 conflicto (duplicado/concurrencia) · 422 validación ·
  500 nunca intencionado.
- Errores SIEMPRE el mismo formato: `{"detail": "mensaje claro en inglés"}`.
- Paginación desde el día 1 en toda lista: `?limit=50&offset=0`, response
  `{"items": [...], "total": n}`. Límite máximo servidor: 200.
- Timestamps ISO-8601 UTC (`2026-06-12T19:30:00Z`). IDs: enteros autoinc o
  UUID — uno de los dos en TODO el proyecto, no mezclar.
- Versionado: prefijo `/api/v1/` desde el principio (renombrar luego es caro).
- Validación: longitud máx de strings SIEMPRE definida; emails/urls con
  formato verificado; números con rangos.
