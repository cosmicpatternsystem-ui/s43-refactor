[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [string]$VerifyScriptPath = 'scripts\verify-readiness-pr.ps1',
    [string]$ReceiptPath = 'out\evidence\readiness-audit-receipt.json'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Require {
    param(
        [Parameter(Mandatory)]
        [bool]$Condition,
        [Parameter(Mandatory)]
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

Set-Location -LiteralPath $RepoRoot

Require (Test-Path -LiteralPath $VerifyScriptPath) "Verify script not found: $VerifyScriptPath"

$receiptDir = Split-Path -Parent $ReceiptPath
if (-not [string]::IsNullOrWhiteSpace($receiptDir)) {
    New-Item -ItemType Directory -Force -Path $receiptDir | Out-Null
}

$verifyOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $VerifyScriptPath -RepoRoot $RepoRoot -EmitJson 2>&1
$verifyExitCode = $LASTEXITCODE
if ($verifyExitCode -ne 0) {
    throw "Verification failed with exit code $verifyExitCode.`n$($verifyOutput | Out-String)"
}

$jsonText = ($verifyOutput | Out-String).Trim()
Require (-not [string]::IsNullOrWhiteSpace($jsonText)) 'Verification returned empty JSON.'

$receipt = $jsonText | ConvertFrom-Json

Require ($receipt.pass -eq $true) 'Receipt indicates a failed audit.'
Require (-not [string]::IsNullOrWhiteSpace($receipt.branch)) 'Receipt missing branch.'
Require (-not [string]::IsNullOrWhiteSpace($receipt.head)) 'Receipt missing head.'
Require (-not [string]::IsNullOrWhiteSpace($receipt.readinessCommit)) 'Receipt missing readinessCommit.'
Require ([int]$receipt.prNumber -gt 0) 'Receipt missing valid prNumber.'
Require ($receipt.prState -eq 'OPEN') "Receipt PR state is not OPEN: $($receipt.prState)"

$finalReceipt = [ordered]@{
    schemaVersion = 1
    auditName = 'readiness-final-audit'
    status = 'PASS'
    generatedAtUtc = [DateTime]::UtcNow.ToString('o')
    receipt = $receipt
}

$finalReceipt | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ReceiptPath -Encoding UTF8

$receiptReloaded = Get-Content -LiteralPath $ReceiptPath -Raw | ConvertFrom-Json
Require ($receiptReloaded.status -eq 'PASS') 'Saved receipt failed validation after reload.'
Require ($receiptReloaded.receipt.pass -eq $true) 'Saved nested receipt failed validation after reload.'

Write-Host "[PASS] Verification JSON captured."
Write-Host "[PASS] Receipt written to $ReceiptPath"
Write-Host "[PASS] Receipt validated after reload."
Write-Host '[PASS] Final readiness audit completed successfully.'
