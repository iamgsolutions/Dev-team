# SKILL: Testing — tests que protegen, no que decoran

- Cada test: UNA cosa, nombre que describe el comportamiento
  (`test_create_note_rejects_empty_title`), patrón AAA (arrange-act-assert).
- Prueba COMPORTAMIENTO por la interfaz pública (el endpoint, la función de
  service) — no internals privados que cambian con cada refactor.
- Por cada función de negocio: caso feliz + 2 tristes mínimo (input inválido,
  recurso inexistente). Los bugs viven en los caminos tristes.
- Deterministas: DB efímera por test/suite (sqlite memoria o tmp), sin red
  real, sin sleeps (usa señales/polling con timeout), sin orden implícito.
- Fixtures para el setup repetido (app, cliente, usuario auth) — en conftest.
- Un bug arreglado = un test que lo habría cazado (regresión).
- Cobertura es un termómetro, no un objetivo: 70% en services/api con tests
  REALES vale más que 95% de tests vacíos.
- Si un test es difícil de escribir, el diseño está acoplado: anótalo en
  NOTES.md como deuda.
