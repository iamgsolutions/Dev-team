# Register the devteam daemon as a Windows scheduled task (24/7).
# Does NOT spend tokens until a project is in an actionable state.
# Run as Administrator. To uninstall: Unregister-ScheduledTask -TaskName "devteam-daemon".

$ErrorActionPreference = "Stop"
# Engine root = parent of this scripts/ folder (works wherever the repo lives).
$work = Split-Path -Parent $PSScriptRoot
$py   = Join-Path $work ".venv\Scripts\python.exe"
$cliArgs = "-m devteam.cli daemon --interval 60"
$user = "$env:USERDOMAIN\$env:USERNAME"

if (-not (Test-Path $py)) { throw "venv not found at $py - create it first (uv venv)" }

$action  = New-ScheduledTaskAction -Execute $py -Argument $cliArgs -WorkingDirectory $work
# Starts at the user's logon; the daemon's own single-instance lock prevents duplicates.
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 2) `
            -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Days 0)
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName "devteam-daemon" -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal -Force -Description "devteam 24/7 dev team daemon"

Write-Host "Task 'devteam-daemon' registered. Start now: Start-ScheduledTask -TaskName devteam-daemon"
Write-Host "Status: devteam panel   |   Stop: Stop-ScheduledTask -TaskName devteam-daemon"
