# SKILL: Accessibility (a11y) — usable by everyone, required by enterprises

## We sell to enterprises; many require accessibility by contract/law.

### The non-negotiables (practical WCAG)
- **Semantics**: use native elements (`<button>`, `<nav>`, `<main>`, `<label>`)
  before a `<div>` with onClick. Correct HTML is accessible for free.
- **Labels**: every input with an associated `<label>` (or `aria-label`). Buttons
  with text (not icon-only; if it's an icon, `aria-label`).
- **Keyboard**: EVERYTHING operable with the mouse must be operable with the
  keyboard (Tab/Enter/Esc). Focus always visible (don't remove the outline
  without replacing it).
- **Contrast**: normal text ≥ 4.5:1, large ≥ 3:1. No light gray on white.
- **Images**: descriptive `alt` (or `alt=""` if decorative).
- **Dynamic state**: important changes (form errors, toasts) announced with
  `aria-live`. Errors tied to the input with `aria-describedby`.

### Forms (where most failures happen)
- Error per field, next to the field, with text (not just red color).
- Don't disable submit without explaining why; validate and show what's missing.

### Quick verification
- Navigate the screen with the KEYBOARD ONLY: can you complete the flow?
- Would screen readers announce every control? (roles/labels present).
- If color is the only cue (red=error), add an icon/text.
