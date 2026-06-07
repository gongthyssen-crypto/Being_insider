Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $root ".runtime"
$pidFile = Join-Path $runtimeDir "backend.pid"
$stdoutLog = Join-Path $runtimeDir "backend.out.log"
$stderrLog = Join-Path $runtimeDir "backend.err.log"
$python = Join-Path $root ".venv\\Scripts\\python.exe"
$backendDir = Join-Path $root "backend"

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

if (Test-Path -LiteralPath $pidFile) {
    [int]$existingPid = Get-Content $pidFile | Select-Object -First 1
    $existingProcess = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
    if ($existingProcess) {
        Write-Host "Backend already running on PID $existingPid"
        exit 0
    }
    if (Test-Path -LiteralPath $pidFile) {
        Microsoft.PowerShell.Management\Remove-Item -LiteralPath $pidFile -Force
    }
}

if (-not (Test-Path $python)) {
    throw "Python environment not found. Run .\\scripts\\setup.ps1 first."
}

$process = Start-Process `
    -FilePath $python `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "18421") `
    -WorkingDirectory $backendDir `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru `
    -WindowStyle Hidden

Microsoft.PowerShell.Management\Set-Content -LiteralPath $pidFile -Value ([string]$process.Id)
Write-Host "Backend started: http://127.0.0.1:18421"
