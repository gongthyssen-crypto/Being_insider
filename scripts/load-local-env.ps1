Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$runtimeEnv = Join-Path $root ".runtime\local-env.ps1"

if (Test-Path -LiteralPath $runtimeEnv) {
    . $runtimeEnv
}
