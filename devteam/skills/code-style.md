# SKILL: Code style — an objective rubric to audit the same way every time

## For the auditor: apply this rubric so your verdict doesn't depend on which
## model you happened to be. For the author: meet it and you'll pass review.

### Style rubric (measurable)
- **Naming**: descriptive, no abbreviations (`getUserNotes`, not `getUN`).
  Functions = verb; variables = noun; booleans = `is/has/can`. English.
- **Size**: function < 40 lines; file < 400; nesting < 4 levels. If it exceeds
  that, extract. (A metric, not an opinion.)
- **Single responsibility**: a function does ONE thing. If its name contains
  "and", it's two functions.
- **No obvious duplication**: the same block 3 times → extract. (But don't
  abstract over 2 trivial uses — cheap duplication > the wrong abstraction.)
- **Comments**: explain the WHY, not the WHAT (the code says the what). Zero
  comments that restate the line. Zero dead commented-out code.
- **No noise**: no debug `console.log`/`print`, no unused imports, no unused
  variables, no TODOs without an issue.
- **Consistency**: follow the file's/project's pattern; don't introduce a new
  style in a module that already has its own.

### Auditor's verdict (the format the engine parses)
```
VERDICT: APPROVED | REJECTED
FINDINGS:
- [critical|major|minor] file:line — what and why
```
- REJECTED if there is ANY critical (security/correctness) — **the engine
  enforces this** (a listed critical overrides an APPROVED verdict). On ≥3 majors,
  write REJECTED and say why.
- Minors are listed, they do NOT block (debt, not defect).
- Be specific: "the code in general…" is not a finding.
