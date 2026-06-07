Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $root ".runtime\\frontend.pid"

if (-not (Test-Path $pidFile)) {
    Write-Host "Frontend is not running."
    exit 0
}

[int]$targetPid = Get-Content $pidFile | Select-Object -First 1
$process = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
if ($process) {
    Stop-Process -Id $targetPid -Force
}

Remove-Item $pidFile -Force
Write-Host "Frontend stopped."
