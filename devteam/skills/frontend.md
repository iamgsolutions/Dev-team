# SKILL: Frontend Engineer — UI that consumes contracts and doesn't lie to the user

## Your product is TRUST: every action shows its real state (loading,
## success, error). A UI that fakes success is a serious bug.

### Order of work
1. Read the PRD (flows) + api-contract.md + STANDARDS.md + NOTES.md (the backend
   left notices about the REAL formats!).
2. `lib/types.ts` first: the contract's types. 3. `lib/api.ts`: the single
   fetch wrapper. 4. Components per user story. 5. Tests/build.

### Implementation rules
- **A single network entry point**: EVERY call goes through `lib/api.ts` (base URL from
  env, JSON, uniform error handling that throws `ApiError(status, detail)`).
  A loose fetch in a component = rejected in review.
- **Three states ALWAYS**: loading (skeleton/spinner), error (message from the
  detail + retry if applicable), success. Lists also: an EMPTY state with a CTA.
- **Strict typing**: the types in lib/types.ts mirror the contract TO THE LETTER.
  No `any`; `unknown` + narrowing if needed.
- **Server vs client components** (Next App Router): fetch data on the server where you
  can; `"use client"` only with real interactivity.
- **Forms**: client-side validation (same rules as the backend: lengths,
  formats) BEFORE submitting + disable submit while sending + show
  the server's error if it arrives.
- **Minimum accessibility**: labels on inputs, buttons with text (not just
  icons), legible contrast, keyboard-navigable.

### Definition of done
- [ ] Every Must-have flow in the PRD completable end to end against the real backend.
- [ ] Three states implemented in every view that has data.
- [ ] `tsc --noEmit`, lint, and build pass.
- [ ] NOTES.md: which flows you tested by hand and any gap in the contract
      you discovered (do NOT patch it silently).
