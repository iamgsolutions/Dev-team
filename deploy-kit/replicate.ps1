# replicate.ps1 - package the engine into a portable zip (no venv/data/secrets).
# Output lands on the Desktop. On the target server: unzip and run
#   Dev-team\deploy-kit\setup.ps1
#
# This packages the ENGINE ONLY. No private memory, no .env, no secrets - by
# design, so the zip is safe to hand to a collaborator.

$ErrorActionPreference = "Stop"
# Engine root = parent of this deploy-kit folder (works wherever the repo lives).
$EngineRoot = Split-Path -Parent $PSScriptRoot
$EngineName = Split-Path -Leaf $EngineRoot

$stamp   = Get-Date -Format "yyyyMMdd-HHmm"
$out     = "$env:USERPROFILE\Desktop\devteam-kit-$stamp.zip"
$staging = Join-Path $env:TEMP "devteam-kit-$stamp"
New-Item -ItemType Directory -Force $staging | Out-Null

# Engine, without runtime or secrets.
robocopy $EngineRoot "$staging\$EngineName" /E `
    /XD .venv data .git __pycache__ .pytest_cache node_modules /XF .env *.log | Out-Null

Compress-Archive -Path "$staging\*" -DestinationPath $out -Force
Remove-Item $staging -Recurse -Force
Write-Host "Portable kit created: $out" -ForegroundColor Green
