# SKILL: Privacidad de datos (GDPR práctico para B2B)

## Si el proyecto toca datos personales (nombres, emails, ubicación, pagos,
## salud), esto NO es opcional — es legal y comercial (vendemos a empresas UE).

### Diseño con privacidad
- **Minimización**: pide y guarda SOLO los datos necesarios para la función.
  ¿Necesitas la fecha de nacimiento o basta "mayor de edad"? Guarda lo mínimo.
- **Marca la PII**: en el data-model, señala qué columnas son datos personales
  (nombre, email, IP, ubicación). El director debe saberlo (decisión de negocio).
- **Base legal**: para cada dato personal, ¿por qué se procesa? (consentimiento,
  contrato, interés legítimo). Consentimiento = explícito, revocable, registrado.
- **Retención**: define cuánto se guarda cada dato y qué lo borra. Nada "para
  siempre por defecto".

### Derechos del usuario (implementables)
- **Acceso/portabilidad**: poder exportar SUS datos (JSON).
- **Borrado** ("derecho al olvido"): poder eliminar su cuenta y datos
  (hard-delete o anonimización, no solo soft-delete si pidió borrado real).
- **Rectificación**: poder corregir sus datos.

### Seguridad de la PII
- Cifrada en tránsito (HTTPS) y, los datos sensibles, en reposo.
- Logs y reportes NUNCA contienen PII en claro (usa ids).
- No compartas PII con terceros (analytics, IA) sin base legal y aviso.

### Regla del director
Cuando detectes PII o una decisión con implicación legal (cookies, tracking,
menores, pagos), ANÓTALO en NOTES.md y escálalo al checkpoint humano. No
decidas tú lo que es responsabilidad legal del negocio.
