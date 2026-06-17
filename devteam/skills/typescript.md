# SKILL: TypeScript — the house style (strict, Next.js)

- `"strict": true` is non-negotiable. Zero `any`; use `unknown` and narrow.
- Domain types in `lib/types.ts`, an EXACT mirror of the api-contract
  (same field names — don't "camelCase" what the API delivers in snake_case).
- Components: function + props typed with an interface. Keep them small (<150 lines);
  if one grows, extract subcomponents or hooks.
- Custom hooks for repeated logic (`useNotes()` encapsulates fetch+state).
  Server state ≠ UI state: don't duplicate API data into editable local state
  without a reason.
- ALWAYS handle promises: `await` with try/catch or `.catch` — floating
  promises = rejection. Typed errors: `if (e instanceof ApiError)`.
- Imports with the `@/` alias (not `../../..`). Named exports (default only for
  Next pages).
- Styles: consistent Tailwind utilities; no loose per-file CSS except
  globals. Generic UI components in `components/ui/`.
- None of: complex logic in JSX (extract variables), indexes as keys in
  mutable lists, `console.log` in final code, silenced useEffect
  dependencies.
