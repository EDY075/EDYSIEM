$ErrorActionPreference = "Stop"
$frontendPath = Join-Path $PSScriptRoot "..\frontend"
$resolvedFrontendPath = (Resolve-Path -LiteralPath $frontendPath).Path

Push-Location -LiteralPath $resolvedFrontendPath
try {
    npm ci
    if ($LASTEXITCODE -ne 0) {
        throw "npm ci failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
