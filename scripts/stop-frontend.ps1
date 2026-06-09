Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $root ".runtime\\frontend.pid"
$frontendPort = 18422

function Get-FrontendPortProcess {
    $connection = Get-NetTCPConnection -LocalPort $frontendPort -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
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

function Test-IsFrontendProcess {
    param(
        [AllowNull()]
        [string]$CommandLine
    )

    if ([string]::IsNullOrWhiteSpace($CommandLine)) {
        return $false
    }

    return $CommandLine -match "vite[\\/]+bin[\\/]+vite\.js" -or $CommandLine -match "--port 18422"
}

if (-not (Test-Path -LiteralPath $pidFile)) {
    $portProcess = Get-FrontendPortProcess
    if ($portProcess -and (Test-IsFrontendProcess $portProcess.CommandLine)) {
        Stop-Process -Id $portProcess.Id -Force
        Write-Host "Frontend stopped."
        exit 0
    }

    Write-Host "Frontend is not running."
    exit 0
}

[int]$targetPid = Get-Content $pidFile | Select-Object -First 1
$process = Get-CimInstance Win32_Process -Filter "ProcessId = $targetPid" -ErrorAction SilentlyContinue
if ($process -and (Test-IsFrontendProcess $process.CommandLine)) {
    Stop-Process -Id $targetPid -Force
}

$portProcess = Get-FrontendPortProcess
if ($portProcess -and $portProcess.Id -ne $targetPid -and (Test-IsFrontendProcess $portProcess.CommandLine)) {
    Stop-Process -Id $portProcess.Id -Force
}

if (Test-Path -LiteralPath $pidFile) {
    Microsoft.PowerShell.Management\Remove-Item -LiteralPath $pidFile -Force
}
Write-Host "Frontend stopped."
