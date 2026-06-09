Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$backendDir = Join-Path $root "backend"

& (Join-Path $PSScriptRoot "load-local-env.ps1")

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python environment not found. Run .\scripts\setup.ps1 first."
}

Push-Location $backendDir
try {
    & $python -m app.build_knowledge_index --all @args
}
finally {
    Pop-Location
}
