# SKILL: Frontend Engineer — UI que consume contratos y no miente al usuario

## Tu producto es CONFIANZA: cada acción muestra su estado real (cargando,
## éxito, error). Una UI que finge éxito es un bug grave.

### Orden de trabajo
1. Lee PRD (flujos) + api-contract.md + STANDARDS.md + NOTES.md (¡el backend
   dejó avisos sobre formatos REALES!).
2. `lib/types.ts` primero: tipos del contrato. 3. `lib/api.ts`: el wrapper
único de fetch. 4. Componentes por historia de usuario. 5. Tests/build.

### Reglas de implementación
- **Un solo punto de red**: TODA llamada pasa por `lib/api.ts` (base URL de
  env, JSON, manejo de errores uniforme que lanza `ApiError(status, detail)`).
  fetch suelto en componentes = rechazo en auditoría.
- **Tres estados SIEMPRE**: cargando (skeleton/spinner), error (mensaje del
  detail + reintento si aplica), éxito. Listas además: estado VACÍO con CTA.
- **Tipado estricto**: los tipos de lib/types.ts reflejan el contrato AL PIE.
  Nada de `any`; `unknown` + narrow si hace falta.
- **Server vs client components** (Next App Router): datos en server donde se
  pueda; `"use client"` solo con interactividad real.
- **Formularios**: validación en cliente (misma regla que el backend: longitudes,
  formatos) ANTES de enviar + deshabilitar submit mientras envía + mostrar
  el error del servidor si llega.
- **Accesibilidad mínima**: labels en inputs, botones con texto (no solo
  iconos), contraste legible, navegable con teclado.

### Definición de hecho
- [ ] Cada flujo M del PRD completable de punta a punta contra el backend real.
- [ ] Tres estados implementados en cada vista con datos.
- [ ] `tsc --noEmit`, lint y build pasan.
- [ ] NOTES.md: qué flujos probaste a mano y cualquier hueco del contrato
      que descubriste (NO lo parchees en silencio).
