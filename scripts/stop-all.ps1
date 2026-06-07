Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = $PSScriptRoot

& (Join-Path $scriptDir "stop-frontend.ps1")
& (Join-Path $scriptDir "stop-backend.ps1")
