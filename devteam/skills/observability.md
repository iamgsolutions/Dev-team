# SKILL: Observabilidad — poder diagnosticar producción sin adivinar

### Logging
- Estructurado (JSON): nivel, timestamp, request-id de correlación, mensaje,
  contexto (qué recurso, qué usuario por id —NO datos personales—, qué pasó).
- Niveles con criterio: ERROR (algo falló y requiere atención), WARN (anómalo
  pero gestionado), INFO (hitos de negocio), DEBUG (solo en desarrollo).
- Una línea por request fallida con TODO el contexto para reproducir.
- NUNCA loguees: secretos, tokens, passwords, cuerpos enteros, PII en claro.

### Health / readiness
- `/health`: el proceso está vivo (siempre 200 si responde).
- `/ready`: las dependencias (DB, Redis) están accesibles (200/503). El
  orquestador/proxy usa este para no enviar tráfico a un pod no listo.

### Errores
- Captura en el borde con contexto suficiente; traduce al formato de error del
  contrato hacia fuera, guarda el detalle técnico en el log interno.
- Agrupa por tipo: un error que se repite 1000 veces es UNA causa, no 1000.
- Si hay Sentry/PostHog configurado, manda el error con su contexto (sin PII).

### Métricas mínimas (cuando el proyecto lo pida)
- Latencia (p50/p95/p99) y tasa de error por endpoint.
- Throughput y saturación de los workers/colas.
- Lo que NO se mide, no se puede mejorar ni alertar.
