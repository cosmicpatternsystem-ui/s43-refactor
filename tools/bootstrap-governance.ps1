#requires -Version 5.1
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$required = @(
    (Join-Path $PSScriptRoot 'governance.ps1'),
    (Join-Path $PSScriptRoot 'governance.config.json'),
    (Join-Path $PSScriptRoot 'governance.schema.json'),
    (Join-Path $PSScriptRoot 'self-test-governance.ps1')
)

foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing required file: $path"
    }
}

$dirs = @(
    (Join-Path $repoRoot 'logs'),
    (Join-Path $repoRoot 'state'),
    (Join-Path $repoRoot 'out'),
    (Join-Path $repoRoot 'quarantine'),
    (Join-Path $repoRoot 'out\evidence')
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

Write-Host "bootstrap-governance: OK"