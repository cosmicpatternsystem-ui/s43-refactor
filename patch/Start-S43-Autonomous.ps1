$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
$Sibling = Split-Path -Parent $Root
$PyFile = Join-Path $Root 'MY_S43_LATEST.py'

if (-not (Test-Path -LiteralPath $PyFile)) {
    throw "Missing runtime file: $PyFile"
}

Set-Location -LiteralPath $Root

if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
    $env:PYTHONPATH = "$Root;$Sibling"
} else {
    $env:PYTHONPATH = "$Root;$Sibling;$env:PYTHONPATH"
}

$env:AUTONOMOUS_AI = 'True'
$env:OPENAI_TRADE_ENABLE = 'True'

Write-Host "AUTONOMOUS_AI=True"
Write-Host "OPENAI_TRADE_ENABLE=True"
Write-Host "Root: $Root"
Write-Host "Sibling: $Sibling"
Write-Host "PYTHONPATH: $env:PYTHONPATH"
Write-Host "Python file: $PyFile"
Write-Host "Launching S43..."

python $PyFile
exit $LASTEXITCODE