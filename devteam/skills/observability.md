# SKILL: Observability — diagnosing production without guessing

### Logging
- Structured (JSON): level, timestamp, correlation request-id, message, context
  (which resource, which user by id —NOT personal data—, what happened).
- Levels with judgment: ERROR (something failed and needs attention), WARN
  (anomalous but handled), INFO (business milestones), DEBUG (development only).
- One line per failed request with ALL the context needed to reproduce it.
- NEVER log: secrets, tokens, passwords, full request bodies, PII in the clear.

### Health / readiness
- `/health`: the process is alive (always 200 if it responds).
- `/ready`: dependencies (DB, Redis) are reachable (200/503). The
  orchestrator/proxy uses this to avoid sending traffic to a pod that isn't ready.

### Errors
- Capture at the edge with enough context; translate to the contract's outward
  error format, and keep the technical detail in the internal log.
- Group by type: an error that repeats 1000 times is ONE cause, not 1000.
- If Sentry/PostHog is configured, send the error with its context (no PII).

### Minimum metrics (when the project calls for it)
- Latency (p50/p95/p99) and error rate per endpoint.
- Throughput and saturation of workers/queues.
- What isn't measured can't be improved or alerted on.
