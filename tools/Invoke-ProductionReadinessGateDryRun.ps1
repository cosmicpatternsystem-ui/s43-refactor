param()

$ErrorActionPreference = "Stop"

$repo = (Get-Location).ProviderPath
[System.Environment]::CurrentDirectory = $repo

$auditPath = "E:\saead\ssl\s43_refactor\AUDIT\PHASE27_PRODUCTION_READINESS_GATE_AND_GO_NO_GO_CHECKLIST_20260616_094021.md"

Write-Output "PHASE27_PRODUCTION_READINESS_GATE_DRY_RUN_START"

$gitStatus = git status --porcelain
$branchStatus = git status -sb
$head = git rev-parse --short HEAD
$remoteHead = git rev-parse --short origin/master

$requiredEvidence = @(
    "AUDIT/COMMERCIAL_MANDATORY_ROADMAP.md",
    "AUDIT/NEXT_ACTION.md"
)

$phaseEvidencePatterns = @(
    "PHASE22_*",
    "PHASE23_*",
    "PHASE24_*",
    "PHASE25_*",
    "PHASE26_*"
)

$evidenceResults = New-Object System.Collections.Generic.List[string]

foreach ($item in $requiredEvidence) {
    $path = Join-Path $repo $item
    if (Test-Path $path) {
        $evidenceResults.Add("FOUND: $item")
    } else {
        $evidenceResults.Add("MISSING: $item")
    }
}

$auditDir = Join-Path $repo "AUDIT"

foreach ($pattern in $phaseEvidencePatterns) {
    $matches = @(
        Get-ChildItem -Path $auditDir -Filter $pattern -File -ErrorAction SilentlyContinue
    )

    if ($matches.Count -gt 0) {
        $evidenceResults.Add("FOUND: AUDIT/$pattern")
    } else {
        $evidenceResults.Add("MISSING: AUDIT/$pattern")
    }
}

$readinessFindings = New-Object System.Collections.Generic.List[string]

if ([string]::IsNullOrWhiteSpace($gitStatus)) {
    $readinessFindings.Add("PASS: Working tree is clean.")
} else {
    $readinessFindings.Add("BLOCKED: Working tree has pending changes.")
}

if ($head -eq $remoteHead) {
    $readinessFindings.Add("PASS: Local HEAD matches origin/master.")
} else {
    $readinessFindings.Add("BLOCKED: Local HEAD does not match origin/master.")
}

$readinessFindings.Add("BLOCKED: Production release remains blocked until platform branch protection is verified.")
$readinessFindings.Add("BLOCKED: Release approval record is not created in this dry-run phase.")
$readinessFindings.Add("BLOCKED: Rollback test evidence is not created in this dry-run phase.")
$readinessFindings.Add("INFO: No deployment, tag creation, secret mutation, or remote setting change was performed.")

$append = @"

## Dry-Run Output

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss K")

### Git State

Branch Status:
```text
$branchStatus

HEAD: $head
Origin Master: $remoteHead

### Evidence Check

text
$($evidenceResults -join [Environment]::NewLine)

### Readiness Findings

text
$($readinessFindings -join [Environment]::NewLine)

### Dry-Run Decision

NO-GO

Production release remains blocked. This phase records the readiness gate only.
"@

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::AppendAllText($auditPath, $append, $utf8NoBom)

Write-Output "PHASE27_PRODUCTION_READINESS_GATE_DRY_RUN_PASS"