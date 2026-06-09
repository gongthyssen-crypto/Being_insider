Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = $PSScriptRoot
$backendHealthUrl = "http://127.0.0.1:18421/api/health"

& (Join-Path $scriptDir "start-backend.ps1")

for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $response = Invoke-RestMethod -Uri $backendHealthUrl -Method Get -TimeoutSec 2
        if ($response.status -eq "ok") {
            break
        }
    }
    catch {
    }

    if ($attempt -eq 29) {
        throw "Backend did not become healthy in time: $backendHealthUrl"
    }

    Start-Sleep -Seconds 1
}

& (Join-Path $scriptDir "start-frontend.ps1")

Write-Host "App ready:"
Write-Host "  Frontend: http://127.0.0.1:18422"
Write-Host "  Backend:  http://127.0.0.1:18421"
