# replicate.ps1 - empaqueta el equipo completo en un zip portable (sin venv/data/secrets).
# Resultado en el Escritorio. En el servidor destino: descomprimir y ejecutar
# hermes-dev-team\deploy-kit\setup.ps1

$stamp = Get-Date -Format "yyyyMMdd-HHmm"
$out = "$env:USERPROFILE\Desktop\devteam-kit-$stamp.zip"
$staging = Join-Path $env:TEMP "devteam-kit-$stamp"
New-Item -ItemType Directory -Force $staging | Out-Null

# Motor (sin runtime ni secretos)
robocopy "C:\Users\Administrator\dev\hermes-dev-team" "$staging\hermes-dev-team" /E `
    /XD .venv data .git __pycache__ .pytest_cache node_modules /XF .env *.log | Out-Null

# Memoria del equipo (documentacion build/ incluida; sin transcripts pesados)
robocopy "C:\Users\Administrator\AppData\Local\hermes\mg-kb" "$staging\memoria-desarrollo-hermes" /E `
    /XD .git /XF *.jsonl | Out-Null

Compress-Archive -Path "$staging\*" -DestinationPath $out -Force
Remove-Item $staging -Recurse -Force
Write-Host "Kit portable creado: $out" -ForegroundColor Green
