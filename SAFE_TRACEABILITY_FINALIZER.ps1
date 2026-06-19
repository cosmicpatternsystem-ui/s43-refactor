$ErrorActionPreference = "Stop"

$Target = ".\s43.py"
$ExpectedHash = "3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$AuditDir = ".\TRACEABILITY_FINALIZER_$Timestamp"

$Roadmap = ".\ROADMAP_vNEXT.md"
$Ledger = ".\CHANGE_CONTROL_LEDGER.jsonl"
$EvidenceJson = ".\PHASE_TRACEABILITY_EVIDENCE.json"
$Closure = ".\TRACEABILITY_CLOSURE_REPORT.md"

New-Item -ItemType Directory -Path $AuditDir -Force | Out-Null

function Find-Matches {
    param([string[]]$Files, [string]$Pattern)

    $results = @()
    foreach ($file in $Files) {
        if (Test-Path $file) {
            $matches = Select-String -Path $file -Pattern $Pattern -CaseSensitive:$false -ErrorAction SilentlyContinue
            foreach ($m in $matches) {
                $results += [pscustomobject]@{
                    file = $file
                    line = $m.LineNumber
                    text = $m.Line.Trim()
                }
            }
        }
    }
    return @($results)
}

function Write-Utf8 {
    param([string]$Path, [string[]]$Lines)
    $Lines | Set-Content -Path $Path -Encoding UTF8
}

function Append-JsonLine {
    param([string]$Path, [hashtable]$Object)
    ($Object | ConvertTo-Json -Compress -Depth 30) | Add-Content -Path $Path -Encoding UTF8
}

if (-not (Test-Path $Target)) {
    throw "s43.py not found. Abort."
}

$ActualHash = (Get-FileHash -Path $Target -Algorithm SHA256).Hash.ToUpperInvariant()
$HashStatus = if ($ActualHash -eq $ExpectedHash) { "PASS" } else { "MISMATCH" }

$Manifest = Join-Path $AuditDir "00_RUN_MANIFEST.txt"
Write-Utf8 $Manifest @(
    "TRACEABILITY FINALIZER RUN MANIFEST",
    "Timestamp: $Timestamp",
    "Target: $Target",
    "Expected SHA256: $ExpectedHash",
    "Actual SHA256:   $ActualHash",
    "Hash status:     $HashStatus",
    "",
    "Safety:",
    "- Does not modify s43.py",
    "- Does not execute s43.py",
    "- Creates/updates documentation and ledger only",
    "- Uses evidence extraction before final status"
)

if ($HashStatus -ne "PASS") {
    Write-Utf8 (Join-Path $AuditDir "ABORT_HASH_MISMATCH.txt") @(
        "ABORTED: HASH MISMATCH",
        "",
        "Expected: $ExpectedHash",
        "Actual:   $ActualHash",
        "",
        "No roadmap/ledger finalization was performed."
    )
    Write-Host "[ABORT] Hash mismatch. No final docs written." -ForegroundColor Red
    Write-Host "Audit folder: $AuditDir"
    exit 2
}

$CandidateFiles = Get-ChildItem -Path . -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Extension -in ".py", ".md", ".txt", ".json", ".jsonl", ".log" } |
    ForEach-Object { $_.FullName }

$PhaseEvidence = [ordered]@{}
for ($i = 1; $i -le 17; $i++) {
    $pattern = "Phase\s*$i|PHASE\s*$i|PHASE_$i|\[Phase $i\]|\[DONE\]\s*Phase $i"
    $PhaseEvidence["phase_$i"] = @(Find-Matches -Files $CandidateFiles -Pattern $pattern)
}

$Missing1To14 = @()
for ($i = 1; $i -le 14; $i++) {
    if ($PhaseEvidence["phase_$i"].Count -eq 0) {
        $Missing1To14 += $i
    }
}

$Phase16Strong = @(Find-Matches -Files @((Resolve-Path $Target).Path) -Pattern "PHASE\s*16|GOVERNANCE ENFORCEMENT|END PHASE 16")
$Phase17Strong = @(Find-Matches -Files $CandidateFiles -Pattern "PHASE\s*17|AUDIT FOUNDATION|END PHASE 17")
$Patch003A = @(Find-Matches -Files $CandidateFiles -Pattern "PATCH_003A|PERFORMANCE_LEDGER_BASELINE|PATCH 003A")

$EvidenceObject = [ordered]@{
    timestamp = $Timestamp
    target = $Target
    expected_sha256 = $ExpectedHash
    actual_sha256 = $ActualHash
    hash_status = $HashStatus
    safety = [ordered]@{
        s43_modified = $false
        s43_executed = $false
        documentation_only = $true
    }
    phase_presence = [ordered]@{}
    missing_phases_1_to_14 = $Missing1To14
    phase_16_strong_evidence = $Phase16Strong
    phase_17_strong_evidence = $Phase17Strong
    patch_003a_evidence = $Patch003A
    user_declared_context = [ordered]@{
        phase_17_second_run = $true
        phase_17_first_run_included_upgrade = $true
        note = "Recorded as user-declared context, not promoted to code evidence unless file markers confirm it."
    }
}

for ($i = 1; $i -le 17; $i++) {
    $EvidenceObject.phase_presence["phase_$i"] = [ordered]@{
        present = ($PhaseEvidence["phase_$i"].Count -gt 0)
        evidence_count = $PhaseEvidence["phase_$i"].Count
        evidence = $PhaseEvidence["phase_$i"]
    }
}

$EvidenceObject | ConvertTo-Json -Depth 30 | Set-Content -Path $EvidenceJson -Encoding UTF8
Copy-Item $EvidenceJson (Join-Path $AuditDir "PHASE_TRACEABILITY_EVIDENCE.json") -Force

if ($Missing1To14.Count -gt 0) {
    Write-Utf8 (Join-Path $AuditDir "ABORT_MISSING_PHASES_1_TO_14.txt") @(
        "ABORTED: PHASES 1..14 ARE NOT FULLY TRACEABLE",
        "",
        "Missing phase evidence: $($Missing1To14 -join ', ')",
        "",
        "No ROADMAP_vNEXT.md or CHANGE_CONTROL_LEDGER.jsonl finalization was performed.",
        "This prevents blind or guessed roadmap normalization."
    )
    Write-Host "[ABORT] Not all phases 1..14 are traceable." -ForegroundColor Red
    Write-Host "Missing: $($Missing1To14 -join ', ')"
    Write-Host "Evidence saved: $EvidenceJson"
    Write-Host "Audit folder: $AuditDir"
    exit 3
}

foreach ($doc in @($Roadmap, $Ledger, $Closure)) {
    if (Test-Path $doc) {
        Copy-Item $doc (Join-Path $AuditDir ("BACKUP_" + (Split-Path $doc -Leaf) + ".$Timestamp.bak")) -Force
    }
}

Write-Utf8 $Roadmap @(
    "# ROADMAP_vNEXT",
    "",
    "Generated: $Timestamp",
    "Mode: Evidence-based traceability finalization",
    "Target baseline: s43.py",
    "Baseline SHA256: $ActualHash",
    "Status: DOCUMENTATION_ONLY / TRACEABLE / NO_SOURCE_CHANGE",
    "",
    "## Safety Position",
    "",
    "- s43.py was not modified.",
    "- s43.py was not executed.",
    "- Baseline hash matched before documentation finalization.",
    "- Phase mapping is evidence-based and avoids guessing.",
    "",
    "## Confirmed Phase Continuity",
    "",
    "Explicit evidence for phases 1 through 14 was found before this roadmap was written.",
    "",
    "## Current Evidence Highlights",
    "",
    "- Phase 16 strong evidence count: $($Phase16Strong.Count)",
    "- Phase 17 strong evidence count: $($Phase17Strong.Count)",
    "- PATCH_003A evidence count: $($Patch003A.Count)",
    "",
    "## Phase 17 Note",
    "",
    "User-declared context: Phase 17 was performed twice; the first run included an upgrade.",
    "This is preserved as historical context and is not treated as confirmed code evidence unless markers confirm it.",
    "",
    "## Next Correct Step",
    "",
    "Proceed with Behavioral Verification after reviewing PHASE_TRACEABILITY_EVIDENCE.json and TRACEABILITY_CLOSURE_REPORT.md.",
    "No blind patching should be performed."
)

Write-Utf8 $Closure @(
    "# Traceability Closure Report",
    "",
    "Generated: $Timestamp",
    "",
    "## Baseline",
    "",
    "- File: s43.py",
    "- Expected SHA256: $ExpectedHash",
    "- Actual SHA256: $ActualHash",
    "- Hash status: $HashStatus",
    "",
    "## Safety Result",
    "",
    "- Source modified: false",
    "- Source executed: false",
    "- Documentation updated: true",
    "- Ledger updated: true",
    "",
    "## Evidence-Based Findings",
    "",
    "- Phases 1 through 14: traceability check passed.",
    "- Phase 16 strong evidence count: $($Phase16Strong.Count)",
    "- Phase 17 strong evidence count: $($Phase17Strong.Count)",
    "- PATCH_003A evidence count: $($Patch003A.Count)",
    "",
    "## Important Governance Note",
    "",
    "This run separates confirmed file evidence, documentation normalization, and user-declared historical context.",
    "The note that Phase 17 was performed twice, with the first run including an upgrade, is preserved in PHASE_TRACEABILITY_EVIDENCE.json.",
    "",
    "## Artifacts",
    "",
    "- ROADMAP_vNEXT.md",
    "- CHANGE_CONTROL_LEDGER.jsonl",
    "- PHASE_TRACEABILITY_EVIDENCE.json",
    "- TRACEABILITY_CLOSURE_REPORT.md",
    "- $AuditDir"
)

$LedgerEntry = @{
    timestamp = $Timestamp
    event = "traceability_finalization"
    target = "s43.py"
    expected_sha256 = $ExpectedHash
    actual_sha256 = $ActualHash
    hash_status = $HashStatus
    source_modified = $false
    source_executed = $false
    docs_written = @("ROADMAP_vNEXT.md", "PHASE_TRACEABILITY_EVIDENCE.json", "TRACEABILITY_CLOSURE_REPORT.md")
    phases_1_to_14_traceable = $true
    missing_phases_1_to_14 = $Missing1To14
    phase_16_evidence_count = $Phase16Strong.Count
    phase_17_evidence_count = $Phase17Strong.Count
    patch_003a_evidence_count = $Patch003A.Count
    user_declared_phase_17_second_run = $true
    user_declared_phase_17_first_run_included_upgrade = $true
    rule = "Evidence first; no blind roadmap promotion."
}

Append-JsonLine $Ledger $LedgerEntry

Copy-Item $Roadmap (Join-Path $AuditDir "ROADMAP_vNEXT.md") -Force
Copy-Item $Ledger (Join-Path $AuditDir "CHANGE_CONTROL_LEDGER.jsonl") -Force
Copy-Item $Closure (Join-Path $AuditDir "TRACEABILITY_CLOSURE_REPORT.md") -Force

Write-Host ""
Write-Host "[PASS] Traceability finalization completed safely." -ForegroundColor Green
Write-Host "Hash: $ActualHash"
Write-Host "Roadmap: $Roadmap"
Write-Host "Ledger: $Ledger"
Write-Host "Evidence: $EvidenceJson"
Write-Host "Closure: $Closure"
Write-Host "Audit folder: $AuditDir"
Write-Host ""
