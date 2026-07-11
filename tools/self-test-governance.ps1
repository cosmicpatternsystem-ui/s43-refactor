#requires -Version 5.1
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$gov = Join-Path $PSScriptRoot 'governance.ps1'
$config = Join-Path $PSScriptRoot 'governance.config.json'
$schema = Join-Path $PSScriptRoot 'governance.schema.json'

foreach ($path in @($gov, $config, $schema)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing required file: $path"
    }
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $gov health-check | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "health-check failed with exit code $LASTEXITCODE"
}

Write-Host "self-test-governance: OK"