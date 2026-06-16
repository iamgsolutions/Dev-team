# SKILL: Estilo de código — rúbrica objetiva para auditar igual siempre

## Para el auditor: aplica esta rúbrica para que tu veredicto no dependa del
## modelo que te tocó ser. Para el que escribe: cúmplela y pasarás review.

### Rúbrica de estilo (medible)
- **Naming**: descriptivo, sin abreviar (`getUserNotes`, no `getUN`). Funciones
  = verbo; variables = sustantivo; booleanos = `is/has/can`. Inglés.
- **Tamaño**: función < 40 líneas; archivo < 400; anidación < 4 niveles. Si se
  pasa, extrae. (Métrica, no opinión.)
- **Una responsabilidad**: una función hace UNA cosa. Si su nombre lleva "y",
  son dos funciones.
- **Sin duplicación evidente**: el mismo bloque 3 veces → extrae. (Pero no
  abstraigas por 2 usos triviales — duplicar barato > abstracción equivocada.)
- **Comentarios**: explican el PORQUÉ, no el QUÉ (el código dice el qué). Cero
  comentarios que repiten la línea. Cero código comentado muerto.
- **Sin ruido**: nada de `console.log`/`print` de depuración, imports sin usar,
  variables sin usar, TODOs sin issue.
- **Consistencia**: sigue el patrón del archivo/proyecto, no introduzcas un
  estilo nuevo en un módulo que ya tiene el suyo.

### Veredicto del auditor (formato que el motor parsea)
```
VEREDICTO: APROBADO | RECHAZADO
HALLAZGOS:
- [crítico|mayor|menor] archivo:línea — qué y por qué
```
- RECHAZADO si: ≥1 crítico (seguridad/corrección) o ≥3 mayores.
- Menores se listan, NO bloquean (deuda, no defecto).
- Sé concreto: "en general el código…" no es un hallazgo.
