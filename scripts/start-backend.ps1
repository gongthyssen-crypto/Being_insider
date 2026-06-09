Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $root ".runtime"
$pidFile = Join-Path $runtimeDir "backend.pid"
$stdoutLog = Join-Path $runtimeDir "backend.out.log"
$stderrLog = Join-Path $runtimeDir "backend.err.log"
$python = Join-Path $root ".venv\\Scripts\\python.exe"
$backendDir = Join-Path $root "backend"
$backendPort = 18421

& (Join-Path $PSScriptRoot "load-local-env.ps1")

function Get-BackendPortProcess {
    $connection = Get-NetTCPConnection -LocalPort $backendPort -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $connection) {
        return $null
    }

    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $($connection.OwningProcess)" -ErrorAction SilentlyContinue
    if (-not $processInfo) {
        return $null
    }

    [pscustomobject]@{
        Id = $connection.OwningProcess
        CommandLine = $processInfo.CommandLine
    }
}

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

$portProcess = Get-BackendPortProcess
if ($portProcess) {
    if ($portProcess.CommandLine -match "uvicorn app\.main:app" -or $portProcess.CommandLine -match "--port 18421") {
        Write-Host "Backend already running on PID $($portProcess.Id)"
        Microsoft.PowerShell.Management\Set-Content -LiteralPath $pidFile -Value ([string]$portProcess.Id)
        exit 0
    }

    throw "Port $backendPort is occupied by PID $($portProcess.Id): $($portProcess.CommandLine)"
}

if (-not (Test-Path $python)) {
    throw "Python environment not found. Run .\\scripts\\setup.ps1 first."
}

$process = Start-Process `
    -FilePath $python `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$backendPort") `
    -WorkingDirectory $backendDir `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru `
    -WindowStyle Hidden

Microsoft.PowerShell.Management\Set-Content -LiteralPath $pidFile -Value ([string]$process.Id)
Write-Host "Backend started: http://127.0.0.1:$backendPort"
