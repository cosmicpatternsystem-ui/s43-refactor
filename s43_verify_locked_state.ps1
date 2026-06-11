param(
    [string]$TargetFile = ".\s43_instrumented_LATEST.py",
    [string]$LockStateFile = ".\S43_LOCK_STATE.json",
    [string]$FinalizationReceipt = ".\S43_CHANGE_PLAN_002_FINALIZATION_RECEIPT.json",
    [string]$LedgerFile = ".\S43_AUDIT_LEDGER.txt",
    [string]$ChangelogFile = ".\S43_CHANGELOG.txt",
    [string]$AttestationFile = ".\S43_CHANGE_PLAN_002_CLOSURE_ATTESTATION.txt"
)

$ErrorActionPreference = "Stop"

$ExpectedHash = "20FB50643AA6A17D950DAAB821072E48132F15FBF6B82646B8BA1390FA237E0F"
$ClosedMarker = "S43_CHANGE_PLAN_002_FORMALLY_CLOSED"
$LockMarker = "S43_LOCKED_AFTER_CHANGE_PLAN_002"

function Assert-FileContains {
    param(
        [string]$PathValue,
        [string]$Needle,
        [string]$Label
    )

    if (-not (Test-Path -LiteralPath $PathValue)) {
        throw "ERROR: missing ${Label}: $PathValue"
    }

    $text = Get-Content -LiteralPath $PathValue -Raw -ErrorAction Stop
    if (-not $text.Contains($Needle)) {
        throw "ERROR: ${Label} missing marker: $Needle"
    }
}

function Invoke-PyCompile {
    param([string]$PathValue)

    $compileOutput = & py -3 -m py_compile $PathValue 2>&1
    if ($LASTEXITCODE -eq 0) {
        return
    }

    $compileOutput = & python -m py_compile $PathValue 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "ERROR: py_compile failed: $compileOutput"
    }
}

if (-not (Test-Path -LiteralPath $TargetFile)) {
    throw "ERROR: target file not found: $TargetFile"
}

$hash = (Get-FileHash -LiteralPath $TargetFile -Algorithm SHA256).Hash.ToUpperInvariant()
if ($hash -ne $ExpectedHash) {
    throw "ERROR: locked hash mismatch. Expected=$ExpectedHash Actual=$hash"
}

Invoke-PyCompile -PathValue $TargetFile

Assert-FileContains -PathValue $LockStateFile -Needle $LockMarker -Label "lock state"
Assert-FileContains -PathValue $FinalizationReceipt -Needle "FINALIZED" -Label "finalization receipt"
Assert-FileContains -PathValue $LedgerFile -Needle $ClosedMarker -Label "audit ledger"
Assert-FileContains -PathValue $ChangelogFile -Needle $ClosedMarker -Label "changelog"
Assert-FileContains -PathValue $AttestationFile -Needle $ClosedMarker -Label "closure attestation"

Write-Host "S43_LOCKED_STATE_VERIFIED"
Write-Host "TARGET_HASH=$hash"
Write-Host "PY_COMPILE=PASSED"
Write-Host "LOCK_MARKER=$LockMarker"
Write-Host "PROJECT_STATE=ROADMAP_CONFORMANT_AUDIT_READY"
Write-Host "NEXT_MUTATION_GATE=S43_CHANGE_PLAN_003"
