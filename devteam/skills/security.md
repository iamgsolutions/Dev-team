# SKILL: Seguridad — mínimos de esta casa (vendemos a empresas)

1. **Secretos**: SOLO en env vars (.env gitignored; .env.example documenta).
   En código/commits/logs = incidente. El gate los escanea: no lo retes.
2. **Inyección**: SQL parametrizado SIEMPRE (ORM). Comandos shell: nunca
   construir con input de usuario. Paths: valida contra traversal (../).
3. **Auth**: passwords con bcrypt/argon2 (NUNCA texto plano ni MD5/SHA1).
   JWT con expiración (≤24h) y secret de env. Endpoints protegidos verifican
   PROPIEDAD (el recurso es del usuario), no solo identidad.
4. **Validación en el borde**: todo input externo (body, query, headers,
   uploads) validado en tipo, formato, longitud y rango ANTES de usarse.
5. **XSS/Output**: frameworks ya escapan — no lo desactives
   (dangerouslySetInnerHTML/| safe solo con sanitizado explícito).
6. **CORS**: orígenes explícitos del entorno, jamás "*" con credenciales.
7. **Errores opacos hacia fuera**: el detail nunca filtra stacktraces,
   rutas internas, versiones ni SQL. El log interno sí lo guarda todo.
8. **Dependencias**: lockfile committeado; añadir una dependencia requiere
   justificarla en NOTES.md (cada una es superficie de ataque).
9. **Datos personales**: si el proyecto los maneja (emails, nombres, pagos),
   anótalo SIEMPRE en NOTES.md — el director debe saberlo (es decisión de
   negocio: GDPR, contratos).
