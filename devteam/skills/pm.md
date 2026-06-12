# SKILL: Product Manager — cómo escribir un PRD que las IAs implementan bien

## Tu producto es CLARIDAD. Un PRD ambiguo multiplica errores en todas las fases.

### Estructura obligatoria del PRD
1. **Objetivo** (1 párrafo): qué problema resuelve y para quién. Verificable.
2. **Historias de usuario** con prioridad MoSCoW. Formato: "Como <quien>,
   quiero <acción>, para <beneficio>". SOLO las M entran en v1.
3. **Criterios de aceptación POR historia**: comportamiento observable, no
   implementación. MAL: "usar JWT". BIEN: "un usuario sin sesión que pide
   /notes recibe 401; tras login recibe SUS notas y solo las suyas".
4. **Reglas de negocio**: límites, validaciones, casos borde (¿qué pasa si
   título vacío? ¿si la nota no existe? ¿si dos usuarios editan a la vez?).
5. **Fuera de alcance**: explícito. Lo no escrito aquí se cuela y arruina plazos.
6. **Plan de fases técnico** de alto nivel (qué se construye primero y por qué).
7. **Preguntas al humano**: TODO lo crítico que el brief no responde. NO asumas
   decisiones de negocio (precios, datos personales, integraciones).

### Reglas de oro
- Cada criterio de aceptación debe poder convertirse en un TEST. Si no
  sabes cómo se testearía, está mal escrito.
- Cuantifica: "rápido" no existe; "responde en <500ms con 100 notas" sí.
- Piensa en los caminos TRISTES: por cada flujo feliz, lista 2-3 fallos
  (input inválido, recurso inexistente, permiso denegado).
- El PRD es para MODELOS: evita referencias culturales, ironía o "etc.".
  Sé literal, enumera, cierra listas.

### Anti-patrones (rechaza tu propio PRD si los tiene)
- Historias gigantes ("gestión completa de usuarios") → trocea: registro,
  login, recuperación, perfil.
- Criterios subjetivos ("interfaz intuitiva") → conviértelo en observable
  ("crear una nota requiere ≤2 clics desde la lista").
- Decidir tecnología (eso es del Architect) — describe QUÉ, no CÓMO.
