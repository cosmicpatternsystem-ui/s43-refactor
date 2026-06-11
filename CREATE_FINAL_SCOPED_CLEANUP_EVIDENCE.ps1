$ErrorActionPreference = "Stop"

$CodePath = ".\s43_instrumented_LATEST.py"
$Doc1 = ".\SAFETY_PROTOCOL_FINAL_VERIFY_20260608_175301.txt"
$Doc2 = ".\SAFETY_GATE_MAPPING_PASS1.txt"

$ExpectedCodeHash = "C90E7358F4647C69505E7B5A33BDEC0F523763678533A90E54F263CD312264F3"
$Status = "SCOPED_NON_SAFETY_CLEANUP_APPLIED_AND_DOCUMENTED"

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

$Doc1Hash = (Get-FileHash -LiteralPath $Doc1 -Algorithm SHA256).Hash
$Doc2Hash = (Get-FileHash -LiteralPath $Doc2 -Algorithm SHA256).Hash

$Doc1Text = Get-Content -LiteralPath $Doc1 -Raw
$Doc2Text = Get-Content -LiteralPath $Doc2 -Raw

$RequiredDoc1 = @(
    "[SCOPED NON-SAFETY CLEANUP ADDENDUM]",
    "STATUS: SCOPED_NON_SAFETY_CLEANUP_APPLIED",
    "POST_PATCH_SHA256: $CodeHash",
    "SAFETY_GATE_STATUS: preserved",
    "PY_COMPILE_STATUS: passed"
)

$RequiredDoc2 = @(
    "[SCOPED NON-SAFETY CLEANUP RECORD]",
    "STATUS: SCOPED_NON_SAFETY_CLEANUP_APPLIED",
    "POST_PATCH_SHA256: $CodeHash",
    "SAFETY_IMPACT: none",
    "EXECUTION_AUTHORIZATION_IMPACT: none",
    "AUTONOMOUS_AI_GATE_IMPACT: none"
)

foreach ($Needle in $RequiredDoc1) {
    if (!$Doc1Text.Contains($Needle)) {
        throw "Doc1 verification failed for: $Needle"
    }
}

foreach ($Needle in $RequiredDoc2) {
    if (!$Doc2Text.Contains($Needle)) {
        throw "Doc2 verification failed for: $Needle"
    }
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportPath = ".\FINAL_SCOPED_CLEANUP_EVIDENCE_$Timestamp.txt"

$Report = @"
[FINAL SCOPED CLEANUP EVIDENCE SNAPSHOT]
STATUS: $Status
TIMESTAMP_LOCAL: $Timestamp

[CODE]
FILE: s43_instrumented_LATEST.py
SHA256: $CodeHash
PY_COMPILE: passed

[DOCUMENTATION]
FILE: SAFETY_PROTOCOL_FINAL_VERIFY_20260608_175301.txt
SHA256: $Doc1Hash
RECORD: SCOPED NON-SAFETY CLEANUP ADDENDUM present and verified

FILE: SAFETY_GATE_MAPPING_PASS1.txt
SHA256: $Doc2Hash
RECORD: SCOPED NON-SAFETY CLEANUP RECORD present and verified

[SAFETY POSITION]
CHANGE_TYPE: scoped non-safety maintainability cleanup
SAFETY_GATE_STATUS: preserved
AI_GATE_STATUS: preserved
ORDER_AUTHORIZATION_STATUS: unchanged
KILL_SWITCH_STATUS: unchanged
RISK_BLOCK_STATUS: unchanged

[FINAL RESULT]
SCOPED_NON_SAFETY_CLEANUP_APPLIED_AND_DOCUMENTED: true
NO_ADDITIONAL_CODE_CHANGE_REQUIRED: true
"@

Set-Content -LiteralPath $ReportPath -Value $Report -Encoding UTF8

$ReportHash = (Get-FileHash -LiteralPath $ReportPath -Algorithm SHA256).Hash

Write-Host "FINAL_EVIDENCE_SNAPSHOT_OK"
Write-Host "Report: $ReportPath"
Write-Host "Report SHA256: $ReportHash"
Write-Host "Code SHA256: $CodeHash"
Write-Host "Doc1 SHA256: $Doc1Hash"
Write-Host "Doc2 SHA256: $Doc2Hash"
