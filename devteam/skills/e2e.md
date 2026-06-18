# SKILL: End-to-end UI testing — see and touch the app like a real user

## Don't infer from the code that the UI works. DRIVE it and watch what happens.
Used by QA (to verify) and Frontend (to self-check before handing off).

### The tool: agent-browser (headless Chrome, agent-native)
The browser control costs NO tokens — only your reasoning does. The loop:
1. `agent-browser open <url>` — load the page.
2. `agent-browser snapshot --json` — accessibility tree + element **refs**
   (e.g. `e2`). This is what you "see"; reason over it. `data.origin` = current URL.
3. Act by ref (deterministic, not brittle CSS selectors):
   `agent-browser click <ref>` · `type <ref> <text>` · `fill <ref> <text>` ·
   `select <ref> <val>` · `press <key>` · `hover <ref>` · `wait <sel|ms>`.
4. ASSERT: re-`snapshot` (did the URL/state change?) or `screenshot <file.png>`
   as evidence.

### What to verify in every user flow
- **The three states**: loading, error, success — all reachable and correct.
- **Force the error state** by mocking the API: `agent-browser route <url> --abort`
  or `route <url> --body <json>`. A flow with no error handling is a defect.
- **Navigation & persistence**: links/buttons go where the PRD says; data survives
  a reload.
- **Performance is a defect too**: `agent-browser vitals --json` (LCP/CLS/INP/
  TTFB/FCP). Flag regressions.
- **Accessibility smoke**: the snapshot IS the accessibility tree — if a control
  has no name/role, screen-reader users can't use it. Flag unnamed controls.
- Always `agent-browser close` when done.

### Anti-patterns / definition of done
- ❌ "It looks right in the code" — you must have DRIVEN it. A screenshot or a
  before/after snapshot is the evidence; a claim without it doesn't count.
- ❌ Testing only the happy path. Every flow's error+loading states get exercised.
- ✅ Done = each PRD user flow walked end to end (UI→API→UI), all three states
  verified, evidence captured, defects (if any) with exact reproduction steps.

### GOTCHA (Windows/PowerShell)
Quote ref selectors: `click '@e2'`, NOT `click @e2` (`@` is splatting in
PowerShell). On bash, `@e2` is fine.
