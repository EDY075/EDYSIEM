# EDY SIEM - inicia o ambiente de desenvolvimento com um comando.
# Uso: .\scripts\dev.ps1            (Windows; abre backend + frontend + seed)
#      .\scripts\dev.ps1 -NoSeed -NoOpen
param(
    [switch]$NoSeed,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    $cmd = @("run.py")
    if ($NoSeed) { $cmd += "--no-seed" }
    if ($NoOpen) { $cmd += "--no-open" }
    python @cmd
    $exit = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $exit