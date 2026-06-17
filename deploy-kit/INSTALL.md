# Deploy Kit — Replicate the dev-team engine on a new server

Guide to stand up the engine (`devteam`) plus the coding brains on another
machine. Estimated time: 20–40 min, most of it spent on logins.

> This kit installs the **engine only** — no private data, no secrets. Each
> operator brings their own brain logins (API keys / subscriptions). Project
> memory lives inside each project repo, not here.

## Server requirements

- Windows Server 2022/2025 (or Windows 11). *(Linux: the engine is pure Python
  and runs fine; the scripts in this kit are PowerShell — porting is trivial,
  see the note at the end.)*
- Internet access and RDP/SSH for the logins.
- **No GPU required.** The brains are external services.

## Automatic install

```powershell
# from PowerShell as Administrator, in the kit folder:
.\setup.ps1
```

The script (idempotent, safe to re-run):
1. Verifies/installs: Node.js LTS, Git, GitHub CLI (winget), uv.
2. Installs the brain CLIs: `@anthropic-ai/claude-code`, `@openai/codex`,
   `opencode-ai`, `@google/gemini-cli` (npm -g).
3. Clones the engine repo (`Dev-team`). Override the URL with
   `$env:DEVTEAM_REPO` if you forked it.
4. Creates the engine venv with uv, installs dependencies, runs the tests.
5. Creates the working structure: `dev\projects\`, `dev\briefs\`.

## Manual steps (logins — always human)

```powershell
gh auth login          # GitHub: if the browser flow fails, use a PAT
claude auth login      # Anthropic (subscription)
codex login            # ChatGPT (subscription)
opencode auth login    # paste your OpenRouter API key (sk-or-...)
gemini                 # Login with Google, then /quit   (optional 4th brain)
```

Verify: `claude auth status`, `codex login status`, `opencode auth list`,
`gh auth status`.

## Subscription guardian configuration

By default the engine rations premium brains: 15 calls/day for Claude, 20 for
Codex (Gemini is disabled by default). Tune it to how the human uses that same
account interactively:

```powershell
$py = "$env:USERPROFILE\dev\Dev-team\.venv\Scripts\python.exe"
& $py -m devteam.cli subs --set claude 10
```

## Final smoke check

```powershell
$py = "$env:USERPROFILE\dev\Dev-team\.venv\Scripts\python.exe"
& $py -m pytest -q                                    # engine suite (run in the engine dir)
& $py -m devteam.cli doctor                           # full harness health check
& $py -m devteam.cli run-task demo --role backend --task "Create hello.md with: Hello" --criteria "hello.md exists"
& $py -m devteam.cli status
```

## Running SEVERAL teams on one server

Each team = one copy of the engine with its own `DEVTEAM_DATA` and
`DEVTEAM_PROJECTS` (environment variables the engine honors):

```powershell
$env:DEVTEAM_DATA = "C:\teams\team2\data"
$env:DEVTEAM_PROJECTS = "C:\teams\team2\projects"
```

With that, registries, budgets and projects are fully isolated per team.

## Linux note

The engine (`devteam`) is pure Python 3.11 with no Windows-only dependencies
(CLI resolution detects `.cmd` wrappers only if they exist). The brain CLIs all
ship official Linux installers. Point `config.py` paths via environment
variables and port `setup.ps1` to bash (~30 lines).
