# setup.ps1 - Set up the DEV-TEAM engine on a fresh Windows machine (idempotent).
# Run as Administrator. See INSTALL.md for full context.
# This sets up the ENGINE only (no private data). Brain logins are done by the human.

$ErrorActionPreference = "Stop"
function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Have($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

$DevRoot   = "$env:USERPROFILE\dev"
$EngineDir = "$DevRoot\Dev-team"
# Engine repo URL (override with $env:DEVTEAM_REPO if you forked it).
$RepoUrl   = if ($env:DEVTEAM_REPO) { $env:DEVTEAM_REPO } else { "git@github.com:iamgsolutions/Dev-team.git" }

Step "1/5 Base tools"
if (-not (Have node)) { winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements }
if (-not (Have git))  { winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements }
if (-not (Have gh))   { winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements }
if (-not (Have uv))   { winget install --id astral-sh.uv -e --accept-source-agreements --accept-package-agreements }
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Step "2/5 Brain CLIs + tools (npm global)"
# OpenCode is the free workhorse; Claude/Codex/Gemini are subscription-backed.
npm install -g @anthropic-ai/claude-code @openai/codex opencode-ai @google/gemini-cli
# agent-browser: agent-driven E2E browser control for the QA/frontend agents.
npm install -g agent-browser
# Download Chrome for Testing for agent-browser (non-fatal if offline).
try { agent-browser install } catch { Write-Host "agent-browser Chrome download skipped: $_" -ForegroundColor Yellow }

Step "3/5 Engine repo"
New-Item -ItemType Directory -Force $DevRoot, "$DevRoot\projects", "$DevRoot\briefs" | Out-Null
if (-not (Test-Path "$EngineDir\.git")) { git clone $RepoUrl $EngineDir }
else { git -C $EngineDir pull }

Step "4/5 Python environment"
Set-Location $EngineDir
uv venv --python 3.11
uv pip install -e ".[dev]"

Step "5/5 Tests"
& "$EngineDir\.venv\Scripts\python.exe" -m pytest -q
if ($LASTEXITCODE -ne 0) { Write-Host "TESTS FAILED - review before using" -ForegroundColor Red }

Write-Host @"

DONE. Remaining manual steps (human logins, once):
  gh auth login            (or a PAT)
  claude auth login
  codex login
  opencode auth login      (OpenRouter API key)
  gemini                   (Login with Google; then /quit)

Verify:   $EngineDir\.venv\Scripts\python.exe -m devteam.cli doctor
Panel:    $EngineDir\.venv\Scripts\python.exe -m devteam.cli panel
"@ -ForegroundColor Green
