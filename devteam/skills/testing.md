# SKILL: Testing — tests that protect, not that decorate

- Each test: ONE thing, a name that describes the behavior
  (`test_create_note_rejects_empty_title`), AAA pattern (arrange-act-assert).
- Test BEHAVIOR through the public interface (the endpoint, the service
  function) — not private internals that change with every refactor.
- For each business function: happy path + 2 sad paths minimum (invalid input,
  nonexistent resource). Bugs live on the sad paths.
- Deterministic: ephemeral DB per test/suite (in-memory sqlite or tmp), no real
  network, no sleeps (use signals/polling with a timeout), no implicit ordering.
- Fixtures for repeated setup (app, client, authenticated user) — in conftest.
- A fixed bug = a test that would have caught it (regression).
- Coverage is a thermometer, not a goal: 70% in services/api with REAL
  tests is worth more than 95% of empty tests.
- If a test is hard to write, the design is coupled: note it in
  NOTES.md as debt.
