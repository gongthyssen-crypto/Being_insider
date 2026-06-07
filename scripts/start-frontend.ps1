Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $root ".runtime"
$pidFile = Join-Path $runtimeDir "frontend.pid"
$stdoutLog = Join-Path $runtimeDir "frontend.out.log"
$stderrLog = Join-Path $runtimeDir "frontend.err.log"
$frontendDir = Join-Path $root "frontend"

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

if (Test-Path -LiteralPath $pidFile) {
    [int]$existingPid = Get-Content $pidFile | Select-Object -First 1
    $existingProcess = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
    if ($existingProcess) {
        Write-Host "Frontend already running on PID $existingPid"
        exit 0
    }
    if (Test-Path -LiteralPath $pidFile) {
        Microsoft.PowerShell.Management\Remove-Item -LiteralPath $pidFile -Force
    }
}

if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    throw "Frontend dependencies not found. Run .\\scripts\\setup.ps1 first."
}

$process = Start-Process `
    -FilePath "npm.cmd" `
    -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1", "--port", "18422", "--strictPort") `
    -WorkingDirectory $frontendDir `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru `
    -WindowStyle Hidden

Microsoft.PowerShell.Management\Set-Content -LiteralPath $pidFile -Value ([string]$process.Id)
Write-Host "Frontend started: http://127.0.0.1:18422"
