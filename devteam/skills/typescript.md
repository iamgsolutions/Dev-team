# SKILL: TypeScript — el estilo de esta casa (strict, Next.js)

- `"strict": true` no negociable. Cero `any`; usa `unknown` y estrecha.
- Tipos del dominio en `lib/types.ts`, espejo EXACTO del api-contract
  (mismos nombres de campos — no "camelices" lo que el API da en snake).
- Componentes: función + props tipadas con interface. Pequeños (<150 líneas);
  si crece, extrae subcomponentes o hooks.
- Hooks propios para lógica repetida (`useNotes()` encapsula fetch+estado).
  Estado servidor ≠ estado UI: no dupliques datos del API en estados locales
  editables sin razón.
- Maneja promesas SIEMPRE: `await` con try/catch o `.catch` — promesas
  flotantes = rechazo. Errores tipados: `if (e instanceof ApiError)`.
- Imports con alias `@/` (no `../../..`). Exports nombrados (default solo
  páginas Next).
- Estilos: Tailwind utilitario consistente; sin CSS suelto por archivo salvo
  globals. Componentes de UI genéricos en `components/ui/`.
- Nada de: lógica en JSX compleja (extrae variables), índices como key en
  listas mutables, `console.log` en código final, dependencias de useEffect
  silenciadas.
