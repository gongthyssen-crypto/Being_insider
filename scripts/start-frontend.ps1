Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $root ".runtime"
$pidFile = Join-Path $runtimeDir "frontend.pid"
$stdoutLog = Join-Path $runtimeDir "frontend.out.log"
$stderrLog = Join-Path $runtimeDir "frontend.err.log"
$frontendDir = Join-Path $root "frontend"
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

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

if (Test-Path -LiteralPath $pidFile) {
    [int]$existingPid = Get-Content $pidFile | Select-Object -First 1
    $existingProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $existingPid" -ErrorAction SilentlyContinue
    if ($existingProcess -and (Test-IsFrontendProcess $existingProcess.CommandLine)) {
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

$portProcess = Get-FrontendPortProcess
if ($portProcess) {
    if (Test-IsFrontendProcess $portProcess.CommandLine) {
        Write-Host "Frontend already running on PID $($portProcess.Id)"
        Microsoft.PowerShell.Management\Set-Content -LiteralPath $pidFile -Value ([string]$portProcess.Id)
        exit 0
    }

    throw "Port $frontendPort is occupied by PID $($portProcess.Id): $($portProcess.CommandLine)"
}

$nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
if (-not $nodeCommand) {
    $nodeCommand = Get-Command node -ErrorAction SilentlyContinue
}
if (-not $nodeCommand) {
    throw "Node.js not found in PATH. Install Node.js or reopen the shell after installation."
}

$viteScript = Join-Path $frontendDir "node_modules\\vite\\bin\\vite.js"
if (-not (Test-Path -LiteralPath $viteScript)) {
    throw "Vite entry file not found. Reinstall frontend dependencies with .\\scripts\\setup.ps1."
}

$process = Start-Process `
    -FilePath $nodeCommand.Source `
    -ArgumentList @($viteScript, "--host", "127.0.0.1", "--port", "$frontendPort", "--strictPort") `
    -WorkingDirectory $frontendDir `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru `
    -WindowStyle Hidden

for ($attempt = 0; $attempt -lt 20; $attempt++) {
    Start-Sleep -Milliseconds 500

    if ($process.HasExited) {
        throw "Frontend failed to start. See $stderrLog for details."
    }

    $listeningProcess = Get-FrontendPortProcess
    if ($listeningProcess -and (Test-IsFrontendProcess $listeningProcess.CommandLine)) {
        Microsoft.PowerShell.Management\Set-Content -LiteralPath $pidFile -Value ([string]$listeningProcess.Id)
        Write-Host "Frontend started: http://127.0.0.1:$frontendPort"
        exit 0
    }
}

if (-not $process.HasExited) {
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
}

throw "Frontend startup timed out while waiting for port $frontendPort."
