$ErrorActionPreference = "Stop"

$CodePath = ".\s43_instrumented_LATEST.py"
$Doc1 = ".\SAFETY_PROTOCOL_FINAL_VERIFY_20260608_175301.txt"
$Doc2 = ".\SAFETY_GATE_MAPPING_PASS1.txt"

$Header1 = "[SCOPED NON-SAFETY CLEANUP ADDENDUM]"
$Header2 = "[SCOPED NON-SAFETY CLEANUP RECORD]"
$ExpectedCodeHash = "C90E7358F4647C69505E7B5A33BDEC0F523763678533A90E54F263CD312264F3"

foreach ($Path in @($CodePath, $Doc1, $Doc2)) {
    if (!(Test-Path -LiteralPath $Path)) {
        throw "Required file not found: $Path"
    }
}

python -m py_compile $CodePath
if ($LASTEXITCODE -ne 0) {
    throw "py_compile failed for $CodePath"
}

$CodeHash = (Get-FileHash -LiteralPath $CodePath -Algorithm SHA256).Hash
if ($CodeHash -ne $ExpectedCodeHash) {
    throw "Unexpected code SHA256. Expected=$ExpectedCodeHash Actual=$CodeHash"
}

$Doc1Text = Get-Content -LiteralPath $Doc1 -Raw
$Doc2Text = Get-Content -LiteralPath $Doc2 -Raw

$Doc1HasRecord = $Doc1Text.Contains($Header1)
$Doc2HasRecord = $Doc2Text.Contains($Header2)

if ($Doc1HasRecord -and $Doc2HasRecord) {
    Write-Host "SCOPED_CLEANUP_RECORD_ALREADY_PRESENT"
    Write-Host "Code SHA256: $CodeHash"
    Select-String -Path $Doc1 -Pattern "\[SCOPED NON-SAFETY CLEANUP ADDENDUM\]|SCOPED_NON_SAFETY_CLEANUP_APPLIED|POST_PATCH_SHA256" -Context 0,2
    Select-String -Path $Doc2 -Pattern "\[SCOPED NON-SAFETY CLEANUP RECORD\]|SCOPED_NON_SAFETY_CLEANUP_APPLIED|POST_PATCH_SHA256" -Context 0,2
    exit 0
}

if ($Doc1HasRecord -xor $Doc2HasRecord) {
    throw "Partial documentation state detected. Doc1HasRecord=$Doc1HasRecord Doc2HasRecord=$Doc2HasRecord"
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$Doc1Backup = "$Doc1.bak_scoped_cleanup_record_$Timestamp"
$Doc2Backup = "$Doc2.bak_scoped_cleanup_record_$Timestamp"

$Doc1BeforeHash = (Get-FileHash -LiteralPath $Doc1 -Algorithm SHA256).Hash
$Doc2BeforeHash = (Get-FileHash -LiteralPath $Doc2 -Algorithm SHA256).Hash

Copy-Item -LiteralPath $Doc1 -Destination $Doc1Backup -Force
Copy-Item -LiteralPath $Doc2 -Destination $Doc2Backup -Force

$Doc1Addendum = @"

[SCOPED NON-SAFETY CLEANUP ADDENDUM]
STATUS: SCOPED_NON_SAFETY_CLEANUP_APPLIED
TARGET_FILE: s43_instrumented_LATEST.py
TARGET_AREA: MarketSnapshotStore._get
TARGET_LINE_AFTER_PATCH: s43_instrumented_LATEST.py:12515
CHANGE_SUMMARY: Removed redundant fallback symbol normalization after _canon_symbol(symbol).
POST_PATCH_SHA256: $CodeHash
SAFETY_SCOPE: non-safety maintainability/state-hygiene cleanup only
SAFETY_GATE_STATUS: preserved
AI_GATE_STATUS: preserved
ORDER_AUTHORIZATION_STATUS: unchanged
KILL_SWITCH_STATUS: unchanged
RISK_BLOCK_STATUS: unchanged
PY_COMPILE_STATUS: passed
BACKUP_CREATED: s43_instrumented_LATEST.py.bak_remove_redundant_market_snapshot_get_20260610_180359
"@

$Doc2Addendum = @"

[SCOPED NON-SAFETY CLEANUP RECORD]
STATUS: SCOPED_NON_SAFETY_CLEANUP_APPLIED
ROADMAP_STATUS: frozen_except_scoped_non_safety_cleanup
SOURCE_EDIT_STATUS: scoped_upgrade_completed
FINAL_CANDIDATE: s43_instrumented_LATEST.py
ROLE_MY_S43_LATEST: reference_only
TARGET_AREA: MarketSnapshotStore._get
CHANGE_SUMMARY: Removed duplicate fallback normalization because _canon_symbol already performs str(...).strip().upper() with exception handling.
POST_PATCH_SHA256: $CodeHash
SAFETY_IMPACT: none
EXECUTION_AUTHORIZATION_IMPACT: none
AUTONOMOUS_AI_GATE_IMPACT: none
HALTED_RISK_BLOCKED_IMPACT: none
VALIDATION: py_compile passed; SHA256 changed after code cleanup; target verification confirmed fallback removed.
"@

try {
    Add-Content -LiteralPath $Doc1 -Value $Doc1Addendum -Encoding UTF8
    Add-Content -LiteralPath $Doc2 -Value $Doc2Addendum -Encoding UTF8

    $Doc1AfterHash = (Get-FileHash -LiteralPath $Doc1 -Algorithm SHA256).Hash
    $Doc2AfterHash = (Get-FileHash -LiteralPath $Doc2 -Algorithm SHA256).Hash

    if ($Doc1AfterHash -eq $Doc1BeforeHash) {
        throw "Doc1 hash unchanged after append"
    }

    if ($Doc2AfterHash -eq $Doc2BeforeHash) {
        throw "Doc2 hash unchanged after append"
    }

    $Doc1Verify = Get-Content -LiteralPath $Doc1 -Raw
    $Doc2Verify = Get-Content -LiteralPath $Doc2 -Raw

    foreach ($Needle in @($Header1, "STATUS: SCOPED_NON_SAFETY_CLEANUP_APPLIED", "POST_PATCH_SHA256: $CodeHash")) {
        if (!$Doc1Verify.Contains($Needle)) {
            throw "Doc1 verification failed for: $Needle"
        }
    }

    foreach ($Needle in @($Header2, "STATUS: SCOPED_NON_SAFETY_CLEANUP_APPLIED", "POST_PATCH_SHA256: $CodeHash")) {
        if (!$Doc2Verify.Contains($Needle)) {
            throw "Doc2 verification failed for: $Needle"
        }
    }

    Write-Host "DOC_PATCH_OK"
    Write-Host "Code SHA256: $CodeHash"
    Write-Host "Doc1 Before SHA256: $Doc1BeforeHash"
    Write-Host "Doc1 After  SHA256: $Doc1AfterHash"
    Write-Host "Doc1 Backup: $Doc1Backup"
    Write-Host "Doc2 Before SHA256: $Doc2BeforeHash"
    Write-Host "Doc2 After  SHA256: $Doc2AfterHash"
    Write-Host "Doc2 Backup: $Doc2Backup"

    Write-Host "`nVerification:"
    Select-String -Path $Doc1 -Pattern "\[SCOPED NON-SAFETY CLEANUP ADDENDUM\]|SCOPED_NON_SAFETY_CLEANUP_APPLIED|POST_PATCH_SHA256" -Context 0,2
    Select-String -Path $Doc2 -Pattern "\[SCOPED NON-SAFETY CLEANUP RECORD\]|SCOPED_NON_SAFETY_CLEANUP_APPLIED|POST_PATCH_SHA256" -Context 0,2
}
catch {
    Copy-Item -LiteralPath $Doc1Backup -Destination $Doc1 -Force
    Copy-Item -LiteralPath $Doc2Backup -Destination $Doc2 -Force
    throw "Patch failed and rollback completed. Reason: $($_.Exception.Message)"
}
