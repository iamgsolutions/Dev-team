# setup.ps1 - Replica el equipo de desarrollo MG en este servidor (idempotente).
# Ejecutar como Administrador. Ver INSTALL.md para el contexto completo.

$ErrorActionPreference = "Stop"
function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Have($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

$DevRoot = "$env:USERPROFILE\dev"
$EngineDir = "$DevRoot\hermes-dev-team"
$KbDir = "$DevRoot\memoria-desarrollo-hermes"

Step "1/6 Herramientas base"
if (-not (Have node)) { winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements }
if (-not (Have git))  { winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements }
if (-not (Have gh))   { winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements }
if (-not (Have uv))   { winget install --id astral-sh.uv -e --accept-source-agreements --accept-package-agreements }
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Step "2/6 CLIs de cerebros (npm global)"
npm install -g @anthropic-ai/claude-code @openai/codex opencode-ai

Step "3/6 Repos (motor + memoria)"
New-Item -ItemType Directory -Force $DevRoot, "$DevRoot\projects", "$DevRoot\briefs" | Out-Null
if (-not (Test-Path "$EngineDir\.git")) { git clone "git@github.com:iamgsolutions/hermes-dev-team.git" $EngineDir }
else { git -C $EngineDir pull }
if (-not (Test-Path "$KbDir\.git")) { git clone "git@github.com:iamgsolutions/memoria-desarrollo-hermes.git" $KbDir }
else { git -C $KbDir pull }

Step "4/6 Entorno Python del motor"
Set-Location $EngineDir
uv venv --python 3.11
uv pip install -e ".[dev]"

Step "5/6 Tests del motor"
& "$EngineDir\.venv\Scripts\python.exe" -m pytest -q
if ($LASTEXITCODE -ne 0) { Write-Host "TESTS FALLARON - revisar antes de usar" -ForegroundColor Red }

Step "6/6 Skill de Hermes (si hay instalacion de Hermes)"
$hermesSkills = "$env:LOCALAPPDATA\hermes\skills"
if (Test-Path $hermesSkills) {
    $dst = "$hermesSkills\software-development\devteam-engine"
    New-Item -ItemType Directory -Force $dst | Out-Null
    Copy-Item "$EngineDir\deploy-kit\hermes-skill\SKILL.md" "$dst\SKILL.md" -Force
    Write-Host "Skill devteam-engine instalada en Hermes."
} else {
    Write-Host "Hermes no detectado en este servidor - skill no instalada (opcional)."
}

Write-Host @"

LISTO. Pasos manuales restantes (logins humanos):
  gh auth login            (o token PAT)
  claude auth login
  codex login
  opencode auth login      (API key de OpenRouter)

Verifica:  $EngineDir\.venv\Scripts\python.exe -m devteam.cli status
Raciones:  ... -m devteam.cli subs --set claude 10
"@ -ForegroundColor Green
