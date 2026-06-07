Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = $PSScriptRoot

& (Join-Path $scriptDir "start-backend.ps1")
Start-Sleep -Seconds 2
& (Join-Path $scriptDir "start-frontend.ps1")

Write-Host "App ready:"
Write-Host "  Frontend: http://127.0.0.1:18422"
Write-Host "  Backend:  http://127.0.0.1:18421"

