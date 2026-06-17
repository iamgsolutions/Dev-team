# SKILL: API design — team conventions (REST)

- Routes: plural nouns, kebab-case: `/notes`, `/user-profiles/{id}`.
  No verbs in routes (`/getNotes` ❌). Nest at most 1 level deep.
- Methods: GET reads (no side effects), POST creates (201 + created object), PUT/PATCH
  updates (200 + object), DELETE removes (204 with no body).
- Status codes: 400 invalid input · 401 unauthenticated · 403 not permitted ·
  404 not found · 409 conflict (duplicate/concurrency) · 422 validation ·
  500 never intentional.
- Errors ALWAYS use the same format: `{"detail": "clear message in English"}`.
- Pagination from day 1 on every list: `?limit=50&offset=0`, response
  `{"items": [...], "total": n}`. Server-side maximum limit: 200.
- Timestamps ISO-8601 UTC (`2026-06-12T19:30:00Z`). IDs: auto-increment integers or
  UUIDs — one of the two across the ENTIRE project, don't mix.
- Versioning: `/api/v1/` prefix from the start (renaming later is expensive).
- Validation: max string length ALWAYS defined; emails/urls with
  verified format; numbers with ranges.
