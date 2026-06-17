# SKILL: Product Manager — how to write a PRD that AIs implement well

## Your product is CLARITY. An ambiguous PRD multiplies errors across every phase.

### Mandatory PRD structure
1. **Objective** (1 paragraph): what problem it solves and for whom. Verifiable.
2. **User stories** with MoSCoW priority. Format: "As a <who>,
   I want <action>, so that <benefit>". ONLY the Musts make it into v1.
3. **Acceptance criteria PER story**: observable behavior, not
   implementation. BAD: "use JWT". GOOD: "an unauthenticated user who requests
   /notes gets a 401; after login they get THEIR notes and only theirs".
4. **Business rules**: limits, validations, edge cases (what happens if the
   title is empty? if the note doesn't exist? if two users edit at the same time?).
5. **Out of scope**: explicit. Anything not written here creeps in and wrecks deadlines.
6. **High-level technical phase plan** (what gets built first and why).
7. **Questions for the human**: EVERYTHING critical the brief doesn't answer. Do NOT assume
   business decisions (pricing, personal data, integrations).

### Golden rules
- Every acceptance criterion must be convertible into a TEST. If you
  don't know how it would be tested, it's poorly written.
- Quantify: "fast" doesn't exist; "responds in <500ms with 100 notes" does.
- Think about the SAD paths: for every happy flow, list 2-3 failures
  (invalid input, nonexistent resource, denied permission).
- The PRD is for MODELS: avoid cultural references, irony, or "etc.".
  Be literal, enumerate, close your lists.

### Anti-patterns (reject your own PRD if it has them)
- Giant stories ("complete user management") → break them up: registration,
  login, recovery, profile.
- Subjective criteria ("intuitive interface") → turn it into something observable
  ("creating a note takes ≤2 clicks from the list").
- Deciding technology (that's the Architect's job) — describe WHAT, not HOW.
