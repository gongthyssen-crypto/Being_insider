Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $root ".runtime\\backend.pid"

if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host "Backend is not running."
    exit 0
}

[int]$targetPid = Get-Content $pidFile | Select-Object -First 1
$process = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
if ($process) {
    Stop-Process -Id $targetPid -Force
}

if (Test-Path -LiteralPath $pidFile) {
    Microsoft.PowerShell.Management\Remove-Item -LiteralPath $pidFile -Force
}
Write-Host "Backend stopped."
