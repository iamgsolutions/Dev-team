# Quickstart — your first project in ~10 minutes

Goal: go from a fresh clone to watching one real phase run, so the whole system
clicks. You do **not** need every brain logged in to explore — OpenCode (the free
workhorse) is enough for the execution phases.

## 0. Prerequisites
- **Python 3.11**, **Node.js 24+**, **git**. (`deploy-kit/setup.ps1` installs
  everything on a fresh Windows box, including the brain CLIs.)
- At least **OpenCode** logged in (`opencode auth login`, paste an OpenRouter key)
  to run execution phases for free. Claude/Codex logins unlock the design phases.

## 1. Install the engine
```powershell
git clone git@github.com:iamgsolutions/Dev-team.git
cd Dev-team
uv venv --python 3.11
uv pip install -e ".[dev]"
.venv\Scripts\python -m pytest -q          # must pass (≈140 tests)
```

## 2. Check the harness (no tokens spent)
```powershell
$py = ".venv\Scripts\python.exe"
& $py -m devteam.cli doctor
```
`doctor` verifies CLIs, credentials, GitHub SSH, the gateway, disk, rations. A
green-ish report means the plumbing is sound; optional lines (jcode, agent-browser)
may say "not installed" and that's fine.

## 3. Create a project from a one-paragraph brief
Write `briefs/notes.md`:
```markdown
# Project Brief — Notes
## 2. Objective
A tiny REST API to create and list short text notes.
## 3. Features
- POST /notes {text} -> creates a note
- GET /notes -> lists notes
## 10. Success criteria
- Both endpoints work and have tests.
```
```powershell
& $py -m devteam.cli new-project briefs\notes.md --name notes --cap 15
& $py -m devteam.cli status notes
```
If the brief is too vague, the engine returns **clarification questions** instead
of guessing — answer them and re-run.

## 4. Run the pipeline, one phase at a time
```powershell
& $py -m devteam.cli run-phase notes      # pm -> writes the PRD, then stops for your approval
```
The pipeline is strict-sequential: `pm → architect → backend → frontend → qa →
deploy → review`. After **pm** and **architect** it **stops at a human
checkpoint**. Read what it produced (in `…\dev\projects\notes\docs\`) and approve:
```powershell
& $py -m devteam.cli approve notes        # accept the PRD -> advances to architect
& $py -m devteam.cli run-phase notes      # architect -> stops again for approval
& $py -m devteam.cli approve notes
& $py -m devteam.cli run-phase notes      # backend (free workhorse) -> gates + audit -> merges
```
Or let the daemon drive it automatically: `& $py -m devteam.cli daemon --interval 60`.

## 5. See the whole picture
```powershell
& $py -m devteam.cli panel        # projects + budget + rations + model scorecard + health
& $py -m devteam.cli log -n 30    # the event flight-recorder (what actually happened)
```

## Where things live
- **Engine code**: `devteam/` (spine = `executor.py`, flow = `pipeline.py`).
- **A project**: `…\dev\projects\<name>\` — its code, plus `.project-memory\`
  (STATE.md / NOTES.md = the team's handoff memory) and `docs\` (PRD, architecture,
  contracts, qa-report).
- **What decides which brain runs**: `docs/05-EXECUTION-POLICY.md`.

## What to read next
1. `00-OVERVIEW.md` — the thesis and honest % complete.
2. `05-EXECUTION-POLICY.md` — exactly what runs when (the routing matrix).
3. `01-ARCHITECTURE.md` → `06-GLOSSARY.md` — module-by-module + vocabulary.
4. `02-EXTENDING.md` — add a skill / role / preset / MCP / brain.
5. `04-COLLABORATION.md` — how we work together (repos, workflow, onboarding).
