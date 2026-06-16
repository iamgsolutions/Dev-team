# Registra el daemon de devteam como tarea programada de Windows (24/7).
# NO lo arranca con tokens hasta que haya un proyecto en estado accionable.
# Ejecutar como Administrador. Para desinstalar: Unregister-ScheduledTask -TaskName "devteam-daemon".

$ErrorActionPreference = "Stop"
$py    = "C:\Users\Administrator\dev\hermes-dev-team\.venv\Scripts\python.exe"
$args  = "-m devteam.cli daemon --interval 60"
$work  = "C:\Users\Administrator\dev\hermes-dev-team"

if (-not (Test-Path $py)) { throw "venv no encontrado en $py — crea el venv primero (uv venv)" }

$action  = New-ScheduledTaskAction -Execute $py -Argument $args -WorkingDirectory $work
# Arranca al iniciar sesión del Administrador; el candado de instancia única
# del propio daemon evita duplicados si se relanza.
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "Administrator"
$settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 2) `
            -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Days 0)
$principal = New-ScheduledTaskPrincipal -UserId "Administrator" -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName "devteam-daemon" -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal -Force -Description "MG devteam 24/7 dev team daemon"

Write-Host "Tarea 'devteam-daemon' registrada. Para arrancar YA: Start-ScheduledTask -TaskName devteam-daemon"
Write-Host "Para ver el estado: devteam panel   ·   Para parar: Stop-ScheduledTask -TaskName devteam-daemon"
