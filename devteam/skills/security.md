# SKILL: Security — this house's minimums (we sell to enterprises)

1. **Secrets**: ONLY in env vars (.env gitignored; .env.example documents them).
   In code/commits/logs = incident. The gate scans for them: don't test it.
2. **Injection**: parameterized SQL ALWAYS (ORM). Shell commands: never
   build them with user input. Paths: validate against traversal (../).
3. **Auth**: passwords with bcrypt/argon2 (NEVER plain text or MD5/SHA1).
   JWT with expiration (≤24h) and a secret from env. Protected endpoints verify
   OWNERSHIP (the resource belongs to the user), not just identity.
4. **Validation at the edge**: all external input (body, query, headers,
   uploads) validated for type, format, length and range BEFORE being used.
5. **XSS/Output**: frameworks already escape — don't disable it
   (dangerouslySetInnerHTML/| safe only with explicit sanitization).
6. **CORS**: explicit origins from the environment, never "*" with credentials.
7. **Opaque errors to the outside**: the detail never leaks stacktraces,
   internal paths, versions or SQL. The internal log does keep everything.
8. **Dependencies**: lockfile committed; adding a dependency requires
   justifying it in NOTES.md (each one is attack surface).
9. **Personal data**: if the project handles it (emails, names, payments),
   ALWAYS note it in NOTES.md — the director must know (it's a business
   decision: GDPR, contracts).
