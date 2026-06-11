param(
    [switch]$Apply,
    [string]$Root = ".",
    [string]$TargetFile = ".\s43_instrumented_LATEST.py",
    [string]$FinalizationReceipt = ".\S43_CHANGE_PLAN_002_FINALIZATION_RECEIPT.json",
    [string]$LedgerFile = ".\S43_AUDIT_LEDGER.txt",
    [string]$ChangelogFile = ".\S43_CHANGELOG.txt",
    [string]$AttestationFile = ".\S43_CHANGE_PLAN_002_CLOSURE_ATTESTATION.txt",
    [string]$LockStateFile = ".\S43_LOCK_STATE.json",
    [string]$GateFile = ".\S43_CHANGE_GATE.txt",
    [string]$VerifyScriptFile = ".\s43_verify_locked_state.ps1",
    [string]$LockReceiptFile = ".\S43_LOCK_RECEIPT.json"
)

$ErrorActionPreference = "Stop"

$PlanId = "S43_CHANGE_PLAN_002"
$ClosedMarker = "S43_CHANGE_PLAN_002_FORMALLY_CLOSED"
$LockMarker = "S43_LOCKED_AFTER_CHANGE_PLAN_002"
$ExpectedAck = "I_APPROVE_LOCK_AFTER_002"

$ExpectedHash = "20FB50643AA6A17D950DAAB821072E48132F15FBF6B82646B8BA1390FA237E0F"
$BeforeHash = "C90E7358F4647C69505E7B5A33BDEC0F523763678533A90E54F263CD312264F3"
$RemovedBytes = 30

function Resolve-Strict {
    param([string]$PathValue, [string]$Label)

    if (-not (Test-Path -LiteralPath $PathValue)) {
        throw "ERROR: $Label not found: $PathValue"
    }

    return (Resolve-Path -LiteralPath $PathValue).Path
}

function Read-RawOrEmpty {
    param([string]$PathValue)

    if (-not (Test-Path -LiteralPath $PathValue)) {
        return ""
    }

    return Get-Content -LiteralPath $PathValue -Raw -ErrorAction Stop
}

function Assert-Contains {
    param([string]$PathValue, [string]$Needle, [string]$Label)

    $text = Read-RawOrEmpty -PathValue $PathValue
    if (-not $text.Contains($Needle)) {
        throw "ERROR: $Label does not contain required marker: $Needle"
    }
}

function Write-NewOrSame {
    param(
        [string]$PathValue,
        [string]$Content,
        [string]$Marker
    )

    if (Test-Path -LiteralPath $PathValue) {
        $existing = Get-Content -LiteralPath $PathValue -Raw -ErrorAction Stop
        if ($existing.Contains($Marker)) {
            Write-Host "SKIP_EXISTING_LOCKED $PathValue"
            return $false
        }

        throw "ERROR: refusing to overwrite existing file without marker: $PathValue"
    }

    Set-Content -LiteralPath $PathValue -Value $Content -Encoding UTF8
    Write-Host "WROTE $PathValue"
    return $true
}

$rootPath = Resolve-Strict -PathValue $Root -Label "root"
$targetPath = Resolve-Strict -PathValue $TargetFile -Label "target file"
$receiptPath = Resolve-Strict -PathValue $FinalizationReceipt -Label "finalization receipt"
$ledgerPath = Resolve-Strict -PathValue $LedgerFile -Label "audit ledger"
$changelogPath = Resolve-Strict -PathValue $ChangelogFile -Label "changelog"
$attestationPath = Resolve-Strict -PathValue $AttestationFile -Label "closure attestation"

$actualHash = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash.ToUpperInvariant()
if ($actualHash -ne $ExpectedHash) {
    throw "ERROR: target hash mismatch. Expected=$ExpectedHash Actual=$actualHash"
}

$compileOutput = & py -3 -m py_compile $targetPath 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "ERROR: py_compile failed: $compileOutput"
}

$receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
if ($receipt.status -ne "FINALIZED") {
    throw "ERROR: finalization receipt status is not FINALIZED"
}
if ($receipt.plan -ne $PlanId) {
    throw "ERROR: finalization receipt plan mismatch"
}
if ($receipt.marker -ne $ClosedMarker) {
    throw "ERROR: finalization receipt marker mismatch"
}
if ($receipt.verified_hash -ne $ExpectedHash) {
    throw "ERROR: finalization receipt verified_hash mismatch"
}
if ($receipt.final_project_state -ne "ROADMAP_CONFORMANT_AUDIT_READY") {
    throw "ERROR: finalization receipt project state mismatch"
}

Assert-Contains -PathValue $ledgerPath -Needle $ClosedMarker -Label "audit ledger"
Assert-Contains -PathValue $changelogPath -Needle $ClosedMarker -Label "changelog"
Assert-Contains -PathValue $attestationPath -Needle $ClosedMarker -Label "closure attestation"

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$lockObject = [ordered]@{
    status = "LOCKED"
    marker = $LockMarker
    locked_after_plan = $PlanId
    locked_at = $timestamp
    root = $rootPath
    target = $targetPath
    target_sha256 = $ExpectedHash
    previous_sha256 = $BeforeHash
    removed_bytes_in_plan_002 = $RemovedBytes
    finalization_receipt = $receiptPath
    audit_ledger = $ledgerPath
    changelog = $changelogPath
    closure_attestation = $attestationPath
    syntax_verification = "py_compile PASSED"
    final_project_state = "ROADMAP_CONFORMANT_AUDIT_READY"
    mutation_policy = "DO_NOT_PATCH_WITHOUT_NEW_PLAN"
    next_required_change_plan = "S43_CHANGE_PLAN_003"
}

$lockJson = $lockObject | ConvertTo-Json -Depth 5

$gateText = @"
S43 CHANGE GATE

STATUS:
LOCKED

MARKER:
$LockMarker

LOCKED_AFTER:
$PlanId

CURRENT_PROJECT_STATE:
ROADMAP_CONFORMANT_AUDIT_READY

LOCKED_TARGET:
s43_instrumented_LATEST.py

LOCKED_SHA256:
$ExpectedHash

POLICY:
DO_NOT_PATCH_WITHOUT_NEW_PLAN

NEXT_MUTATION_GATE:
S43_CHANGE_PLAN_003

REQUIRED_BEFORE_ANY_FUTURE_CHANGE:
1. Open S43_CHANGE_PLAN_003.
2. Record purpose, scope, expected files, rollback path, and validation plan.
3. Verify current locked SHA256 before mutation.
4. Apply only after explicit unlock acknowledgement for the new plan.
5. Produce new closure attestation and receipt after completion.

$LockMarker
"@

$verifyScript = @"
param(
    [string]`$TargetFile = ".\s43_instrumented_LATEST.py",
    [string]`$LockStateFile = ".\S43_LOCK_STATE.json",
    [string]`$FinalizationReceipt = ".\S43_CHANGE_PLAN_002_FINALIZATION_RECEIPT.json",
    [string]`$LedgerFile = ".\S43_AUDIT_LEDGER.txt",
    [string]`$ChangelogFile = ".\S43_CHANGELOG.txt",
    [string]`$AttestationFile = ".\S43_CHANGE_PLAN_002_CLOSURE_ATTESTATION.txt"
)

`$ErrorActionPreference = "Stop"

`$ExpectedHash = "$ExpectedHash"
`$ClosedMarker = "$ClosedMarker"
`$LockMarker = "$LockMarker"

function Assert-FileContains {
    param([string]`$PathValue, [string]`$Needle, [string]`$Label)

    if (-not (Test-Path -LiteralPath `$PathValue)) {
        throw "ERROR: missing `$Label`: `$PathValue"
    }

    `$text = Get-Content -LiteralPath `$PathValue -Raw -ErrorAction Stop
    if (-not `$text.Contains(`$Needle)) {
        throw "ERROR: `$Label missing marker: `$Needle"
    }
}

if (-not (Test-Path -LiteralPath `$TargetFile)) {
    throw "ERROR: target file not found: `$TargetFile"
}

`$hash = (Get-FileHash -LiteralPath `$TargetFile -Algorithm SHA256).Hash.ToUpperInvariant()
if (`$hash -ne `$ExpectedHash) {
    throw "ERROR: locked hash mismatch. Expected=`$ExpectedHash Actual=`$hash"
}

`$compileOutput = & py -3 -m py_compile `$TargetFile 2>&1
if (`$LASTEXITCODE -ne 0) {
    throw "ERROR: py_compile failed: `$compileOutput"
}

Assert-FileContains -PathValue `$LockStateFile -Needle `$LockMarker -Label "lock state"
Assert-FileContains -PathValue `$FinalizationReceipt -Needle "FINALIZED" -Label "finalization receipt"
Assert-FileContains -PathValue `$LedgerFile -Needle `$ClosedMarker -Label "audit ledger"
Assert-FileContains -PathValue `$ChangelogFile -Needle `$ClosedMarker -Label "changelog"
Assert-FileContains -PathValue `$AttestationFile -Needle `$ClosedMarker -Label "closure attestation"

Write-Host "S43_LOCKED_STATE_VERIFIED"
Write-Host "TARGET_HASH=`$hash"
Write-Host "PY_COMPILE=PASSED"
Write-Host "LOCK_MARKER=`$LockMarker"
Write-Host "PROJECT_STATE=ROADMAP_CONFORMANT_AUDIT_READY"
Write-Host "NEXT_MUTATION_GATE=S43_CHANGE_PLAN_003"
"@

$lockReceiptObject = [ordered]@{
    status = "LOCK_APPLIED"
    marker = $LockMarker
    timestamp = $timestamp
    locked_after_plan = $PlanId
    target = $targetPath
    target_sha256 = $ExpectedHash
    finalization_receipt = $receiptPath
    lock_state_file = $LockStateFile
    gate_file = $GateFile
    verify_script = $VerifyScriptFile
    final_project_state = "ROADMAP_CONFORMANT_AUDIT_READY"
    next_mutation_gate = "S43_CHANGE_PLAN_003"
}

$lockReceiptJson = $lockReceiptObject | ConvertTo-Json -Depth 5

Write-Host "S43_LOCK_AFTER_CHANGE_PLAN_002_SAFE"
if ($Apply) {
    Write-Host "MODE=APPLY"
} else {
    Write-Host "MODE=DRY_RUN"
}
Write-Host "ROOT=$rootPath"
Write-Host "TARGET=$targetPath"
Write-Host "TARGET_HASH=$actualHash"
Write-Host "FINALIZATION_RECEIPT=$receiptPath"
Write-Host "LEDGER=$ledgerPath"
Write-Host "CHANGELOG=$changelogPath"
Write-Host "ATTESTATION=$attestationPath"
Write-Host "PY_COMPILE=PASSED"
Write-Host "LOCK_STATE_FILE=$LockStateFile"
Write-Host "GATE_FILE=$GateFile"
Write-Host "VERIFY_SCRIPT_FILE=$VerifyScriptFile"
Write-Host "LOCK_RECEIPT_FILE=$LockReceiptFile"

if (-not $Apply) {
    Write-Host ""
    Write-Host "DRY_RUN_ONLY"
    Write-Host "To apply:"
    Write-Host '  $env:S43_LOCK_ACK = "I_APPROVE_LOCK_AFTER_002"'
    Write-Host '  powershell -ExecutionPolicy Bypass -File .\s43_lock_after_cp002_safe.ps1 -Apply'
    exit 0
}

if ($env:S43_LOCK_ACK -ne $ExpectedAck) {
    throw "ERROR: apply requires S43_LOCK_ACK=I_APPROVE_LOCK_AFTER_002"
}

$lockChanged = Write-NewOrSame -PathValue $LockStateFile -Content $lockJson -Marker $LockMarker
$gateChanged = Write-NewOrSame -PathValue $GateFile -Content $gateText -Marker $LockMarker
$verifyChanged = Write-NewOrSame -PathValue $VerifyScriptFile -Content $verifyScript -Marker $LockMarker
$receiptChanged = Write-NewOrSame -PathValue $LockReceiptFile -Content $lockReceiptJson -Marker $LockMarker

Write-Host "LOCK_APPLIED_SAFELY"
Write-Host "LOCK_STATE_CHANGED=$lockChanged"
Write-Host "GATE_CHANGED=$gateChanged"
Write-Host "VERIFY_SCRIPT_CHANGED=$verifyChanged"
Write-Host "LOCK_RECEIPT_CHANGED=$receiptChanged"
Write-Host "FINAL_STATUS=$LockMarker"
Write-Host "PROJECT_STATE=ROADMAP_CONFORMANT_AUDIT_READY"
Write-Host "NEXT_MUTATION_GATE=S43_CHANGE_PLAN_003"
