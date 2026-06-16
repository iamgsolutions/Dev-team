# SKILL: Flujo Git — ramas, commits y PRs consistentes en todo el equipo

### Ramas
- El motor crea tu rama (`task/<slug>`); trabaja SOLO en ella, nunca en main.
- Una rama = una tarea = una intención. No mezcles features.

### Commits
- Convencionales: `feat:`, `fix:`, `test:`, `docs:`, `chore:`, `refactor:`,
  `perf:`. En inglés, imperativo, primera línea < 72 chars.
- Atómicos: cada commit deja el repo compilando y con sentido. Separa "cambio
  de comportamiento" de "cambio de forma" (refactor) en commits distintos.
- El cuerpo explica el PORQUÉ si no es obvio. El motor añade el trailer
  `Model:`/`Role:` automáticamente — no lo dupliques.

### Pull Requests (cuando se publiquen en GitHub)
- Título = el cambio en una línea. Cuerpo con 3 secciones:
  **Qué** (cambié), **Por qué** (motivo/issue), **Cómo probarlo** (pasos/tests).
- Lista riesgos conocidos y deuda que dejas.
- PR pequeño y enfocado > PR gigante. Si toca >15 archivos no triviales,
  probablemente había que partirlo.

### Qué va dónde
- En el COMMIT: el cambio y su porqué técnico.
- En NOTES.md: decisiones, dudas, avisos al siguiente agente, deuda técnica.
- En docs/adr/: decisiones de arquitectura que no se reabren sin discusión.
- NUNCA en git: secretos (.env), artefactos de build, dependencias (node_modules).
