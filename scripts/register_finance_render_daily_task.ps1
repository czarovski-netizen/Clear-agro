param(
    [string]$TaskName = "ClearOS-Finance-Render-Daily",
    [string]$StartTime = "06:50",
    [string[]]$PushRemotes = @("fork", "origin")
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PythonExe = "C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe"
$ScriptPath = Join-Path $RepoRoot "scripts\publish_finance_render_snapshot.py"
$LogDir = Join-Path $RepoRoot "logs\integration\scheduler"
$LogFile = Join-Path $LogDir "finance_render_daily.log"
$WrapperDir = Join-Path $RepoRoot "automation\jobs"
$WrapperCmd = Join-Path $WrapperDir "run_finance_render_daily.cmd"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
New-Item -ItemType Directory -Path $WrapperDir -Force | Out-Null

if (-not (Test-Path $ScriptPath)) {
    throw "Script nao encontrado: $ScriptPath"
}

$pushArgs = @()
foreach ($remote in $PushRemotes) {
    if (-not [string]::IsNullOrWhiteSpace($remote)) {
        $pushArgs += "--push-remote $remote"
    }
}

$wrapperBody = @(
    "@echo off",
    "cd /d `"$RepoRoot`"",
    "`"$PythonExe`" `"$ScriptPath`" $($pushArgs -join ' ') >> `"$LogFile`" 2>&1"
)
Set-Content -Path $WrapperCmd -Value $wrapperBody -Encoding ASCII

$cmd = "`"$WrapperCmd`""
schtasks /Create /TN $TaskName /SC DAILY /ST $StartTime /TR $cmd /F | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao registrar task no schtasks (exit code $LASTEXITCODE)."
}

Write-Output "Task registrada: $TaskName"
Write-Output "Horario: $StartTime"
Write-Output "Wrapper: $WrapperCmd"
