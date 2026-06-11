param(
    [switch]$Apply,
    [string]$Root = ".",
    [string]$TargetFile = ".\s43_instrumented_LATEST.py",
    [string]$BackupDir = ".\.s43_cycle002_backup_20260611_183318",
    [string]$LedgerFile = ".\S43_AUDIT_LEDGER.txt",
    [string]$ChangelogFile = ".\S43_CHANGELOG.txt",
    [string]$AttestationFile = ".\S43_CHANGE_PLAN_002_CLOSURE_ATTESTATION.txt",
    [string]$ReceiptFile = ".\S43_CHANGE_PLAN_002_FINALIZATION_RECEIPT.json"
)

$ErrorActionPreference = "Stop"

$PlanId = "S43_CHANGE_PLAN_002"
$Marker = "S43_CHANGE_PLAN_002_FORMALLY_CLOSED"
$ExpectedAck = "I_APPROVE_FINALIZE_002"

$BeforeHash = "C90E7358F4647C69505E7B5A33BDEC0F523763678533A90E54F263CD312264F3"
$AfterHash  = "20FB50643AA6A17D950DAAB821072E48132F15FBF6B82646B8BA1390FA237E0F"
$RemovedBytes = 30

function Resolve-ExistingPathStrict {
    param([string]$PathValue, [string]$Label)

    if (-not (Test-Path -LiteralPath $PathValue)) {
        throw "ERROR: $Label not found: $PathValue"
    }

    return (Resolve-Path -LiteralPath $PathValue).Path
}

function Test-FileContains {
    param([string]$PathValue, [string]$Needle)

    if (-not (Test-Path -LiteralPath $PathValue)) {
        return $false
    }

    $content = Get-Content -LiteralPath $PathValue -Raw -ErrorAction Stop
    return $content.Contains($Needle)
}

function Append-Once {
    param(
        [string]$PathValue,
        [string]$Entry,
        [string]$Needle
    )

    if (Test-FileContains -PathValue $PathValue -Needle $Needle) {
        Write-Host "SKIP_DUPLICATE $PathValue"
        return $false
    }

    Add-Content -LiteralPath $PathValue -Value $Entry -Encoding UTF8
    Write-Host "APPENDED $PathValue"
    return $true
}

$rootPath = Resolve-ExistingPathStrict -PathValue $Root -Label "root"
$targetPath = Resolve-ExistingPathStrict -PathValue $TargetFile -Label "target file"
$backupPath = Resolve-ExistingPathStrict -PathValue $BackupDir -Label "backup directory"

$actualHash = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash.ToUpperInvariant()
if ($actualHash -ne $AfterHash) {
    throw "ERROR: target hash mismatch. Expected=$AfterHash Actual=$actualHash"
}

$compileCheck = & py -3 -m py_compile $targetPath 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "ERROR: py_compile failed: $compileCheck"
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$today = Get-Date -Format "yyyy-MM-dd"

$ledgerEntry = @"
ROADMAP / AUDIT LEDGER ENTRY
Plan: $PlanId
Timestamp: $timestamp
Marker: $Marker

$PlanId was opened after the project had already reached
ROADMAP_CONFORMANT_AUDIT_READY state, solely to address previously identified
cosmetic excessive blank-run candidates.

Scope:
s43_instrumented_LATEST.py only

Change type:
Cosmetic blank-run normalization only

Method:
Safe line-based normalization with fail-closed validation.

Integrity:
All non-empty lines were preserved byte-for-byte. Only surplus blank-line bytes
were removed. No behavioral, structural, semantic, or runtime-intent change was
introduced.

Verification:
py_compile passed successfully.

Before SHA256:
$BeforeHash

After SHA256:
$AfterHash

Removed bytes:
$RemovedBytes

Backup:
$backupPath

Final status:
$Marker
PROJECT_STATE_RETURNED_TO_ROADMAP_CONFORMANT_AUDIT_READY

----
"@

$changelogEntry = @"
$today - S43 Change Plan 002
Marker: $Marker

Changed:
- Normalized excessive blank-line runs in s43_instrumented_LATEST.py.
- Removed $RemovedBytes bytes of surplus blank-line content.
- Preserved all non-empty code/content lines byte-for-byte.

Validation:
- Applied with explicit unlock acknowledgement:
  S43_UNLOCK_ACK=I_APPROVE_CYCLE_002
- Finalized with explicit unlock acknowledgement:
  S43_FINALIZE_ACK=I_APPROVE_FINALIZE_002
- Used safe line-based patching with fail-closed non-empty-content guard.
- py_compile passed successfully.
- Final SHA256 matched expected audit hash.

Hashes:
- Before:
  $BeforeHash
- After:
  $AfterHash

Backup:
- $backupPath

Status:
- Cosmetic-only cleanup completed.
- No behavioral change introduced.
- $Marker
- S43 returned to ROADMAP_CONFORMANT_AUDIT_READY state.

----
"@

$attestationEntry = @"
S43_CHANGE_PLAN_002_CLOSURE_ATTESTATION

STATUS: FORMALLY_ATTESTED
PLAN: $PlanId
TIMESTAMP: $timestamp
MARKER: $Marker

SCOPE:
s43_instrumented_LATEST.py only

CHANGE_TYPE:
Cosmetic blank-run normalization only

METHOD:
Safe line-based patch with fail-closed guard

NON_EMPTY_CONTENT_CHANGE:
None

BEHAVIORAL_CHANGE:
None

STRUCTURAL_CHANGE:
None

SYNTAX_VERIFICATION:
PASSED via py_compile

BACKUP_DIR:
$backupPath

BEFORE_SHA256:
$BeforeHash

AFTER_SHA256:
$AfterHash

REMOVED_BYTES:
$RemovedBytes

RESULT:
CHANGE_PLAN_002_EXECUTED_SUCCESSFULLY
AUDIT_TRAIL_COMPLETE
PROJECT_STATE_RETURNED_TO_ROADMAP_CONFORMANT_AUDIT_READY
$Marker
"@

Write-Host "S43_CHANGE_PLAN_002_FINALIZATION_SAFE"
if ($Apply) {
    Write-Host "MODE=APPLY"
} else {
    Write-Host "MODE=DRY_RUN"
}
Write-Host "ROOT=$rootPath"
Write-Host "TARGET=$targetPath"
Write-Host "TARGET_HASH=$actualHash"
Write-Host "BACKUP_DIR=$backupPath"
Write-Host "LEDGER_FILE=$LedgerFile"
Write-Host "CHANGELOG_FILE=$ChangelogFile"
Write-Host "ATTESTATION_FILE=$AttestationFile"
Write-Host "RECEIPT_FILE=$ReceiptFile"
Write-Host "PY_COMPILE=PASSED"

$ledgerDuplicate = Test-FileContains -PathValue $LedgerFile -Needle $Marker
$changelogDuplicate = Test-FileContains -PathValue $ChangelogFile -Needle $Marker
$attestationDuplicate = Test-FileContains -PathValue $AttestationFile -Needle $Marker

Write-Host "LEDGER_DUPLICATE=$ledgerDuplicate"
Write-Host "CHANGELOG_DUPLICATE=$changelogDuplicate"
Write-Host "ATTESTATION_DUPLICATE=$attestationDuplicate"

if (-not $Apply) {
    Write-Host ""
    Write-Host "DRY_RUN_ONLY"
    Write-Host "To apply:"
    Write-Host '  $env:S43_FINALIZE_ACK = "I_APPROVE_FINALIZE_002"'
    Write-Host '  powershell -ExecutionPolicy Bypass -File .\s43_finalize_change_plan_002_safe.ps1 -Apply'
    exit 0
}

if ($env:S43_FINALIZE_ACK -ne $ExpectedAck) {
    throw "ERROR: apply requires S43_FINALIZE_ACK=I_APPROVE_FINALIZE_002"
}

$ledgerChanged = Append-Once -PathValue $LedgerFile -Entry $ledgerEntry -Needle $Marker
$changelogChanged = Append-Once -PathValue $ChangelogFile -Entry $changelogEntry -Needle $Marker

if ($attestationDuplicate) {
    Write-Host "SKIP_DUPLICATE $AttestationFile"
    $attestationChanged = $false
} else {
    Set-Content -LiteralPath $AttestationFile -Value $attestationEntry -Encoding UTF8
    Write-Host "WROTE $AttestationFile"
    $attestationChanged = $true
}

$receiptObject = [ordered]@{
    status = "FINALIZED"
    plan = $PlanId
    marker = $Marker
    timestamp = $timestamp
    root = $rootPath
    target = $targetPath
    before_sha256 = $BeforeHash
    after_sha256 = $AfterHash
    verified_hash = $actualHash
    removed_bytes = $RemovedBytes
    backup_dir = $backupPath
    py_compile = "PASSED"
    ledger_file = $LedgerFile
    changelog_file = $ChangelogFile
    attestation_file = $AttestationFile
    ledger_changed = $ledgerChanged
    changelog_changed = $changelogChanged
    attestation_changed = $attestationChanged
    final_project_state = "ROADMAP_CONFORMANT_AUDIT_READY"
}

$receiptJson = $receiptObject | ConvertTo-Json -Depth 4
Set-Content -LiteralPath $ReceiptFile -Value $receiptJson -Encoding UTF8

Write-Host "FINALIZATION_APPLIED_SAFELY"
Write-Host "RECEIPT=$ReceiptFile"
Write-Host "FINAL_STATUS=$Marker"
Write-Host "PROJECT_STATE=ROADMAP_CONFORMANT_AUDIT_READY"
