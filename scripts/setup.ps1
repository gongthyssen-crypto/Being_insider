Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

Push-Location $root
try {
    Write-Host "[setup] Creating uv environment with Python 3.11"
    uv venv --python 3.11 .venv

    Write-Host "[setup] Syncing backend dependencies"
    uv sync --python 3.11

    Write-Host "[setup] Installing frontend dependencies"
    npm install --prefix frontend

    Write-Host "[setup] Done"
}
finally {
    Pop-Location
}

