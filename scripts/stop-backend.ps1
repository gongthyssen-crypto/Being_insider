Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $root ".runtime\\backend.pid"
$backendPort = 18421

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

if (-not (Test-Path -LiteralPath $pidFile)) {
    $portProcess = Get-BackendPortProcess
    if ($portProcess -and ($portProcess.CommandLine -match "uvicorn app\.main:app" -or $portProcess.CommandLine -match "--port 18421")) {
        Stop-Process -Id $portProcess.Id -Force
        Write-Host "Backend stopped."
        exit 0
    }

    Write-Host "Backend is not running."
    exit 0
}

[int]$targetPid = Get-Content $pidFile | Select-Object -First 1
$process = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
if ($process) {
    Stop-Process -Id $targetPid -Force
}

$portProcess = Get-BackendPortProcess
if ($portProcess -and $portProcess.Id -ne $targetPid -and ($portProcess.CommandLine -match "uvicorn app\.main:app" -or $portProcess.CommandLine -match "--port 18421")) {
    Stop-Process -Id $portProcess.Id -Force
}

if (Test-Path -LiteralPath $pidFile) {
    Microsoft.PowerShell.Management\Remove-Item -LiteralPath $pidFile -Force
}
Write-Host "Backend stopped."
