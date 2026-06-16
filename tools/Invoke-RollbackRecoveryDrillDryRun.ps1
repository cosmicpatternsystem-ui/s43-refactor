param()

$ErrorActionPreference = "Stop"

$repo = (Get-Location).ProviderPath
[System.Environment]::CurrentDirectory = $repo

$auditPath = 'E:\saead\ssl\s43_refactor\AUDIT\PHASE28_ROLLBACK_STRATEGY_AND_RECOVERY_DRILL_DRY_RUN_20260616_095138.md'

Write-Output "PHASE28_ROLLBACK_RECOVERY_DRILL_DRY_RUN_START"

$gitStatus = git status --porcelain
$branchStatus = git status -sb
$head = git rev-parse --short HEAD
$previousCommit = git rev-parse --short HEAD~1
$remoteHead = git rev-parse --short origin/master

$evidencePatterns = @(
    "AUDIT/PHASE25_ARTIFACT_MANIFEST_DRY_RUN.txt",
    "AUDIT/PHASE25_ARTIFACT_SHA256_DRY_RUN.txt",
    "AUDIT/PHASE26_*",
    "AUDIT/PHASE27_*",
    "AUDIT/COMMERCIAL_MANDATORY_ROADMAP.md",
    "AUDIT/NEXT_ACTION.md"
)

$evidenceResults = New-Object System.Collections.Generic.List[string]

foreach ($pattern in $evidencePatterns) {
    $fullPattern = Join-Path $repo $pattern
    $parent = Split-Path $fullPattern -Parent
    $leaf = Split-Path $fullPattern -Leaf

    if (Test-Path $parent) {
        $matches = @(Get-ChildItem -Path $parent -Filter $leaf -File -ErrorAction SilentlyContinue)
    } else {
        $matches = @()
    }

    if ($matches.Count -gt 0) {
        $evidenceResults.Add("FOUND: $pattern")
    } else {
        $evidenceResults.Add("MISSING: $pattern")
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

$readinessFindings.Add("INFO: Current HEAD is $head.")
$readinessFindings.Add("INFO: Previous commit candidate is $previousCommit.")
$readinessFindings.Add("BLOCKED: Real rollback remains blocked without approval record.")
$readinessFindings.Add("BLOCKED: Rollback command path is not executed in dry-run.")
$readinessFindings.Add("BLOCKED: Data rollback and migration safety evidence is not created in this phase.")
$readinessFindings.Add("INFO: No deployment, tag mutation, secret mutation, or remote setting change was performed.")

$append = @"

## Dry-Run Output

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss K")

### Git State

Branch Status:
```text
$branchStatus

HEAD: $head
Previous Commit Candidate: $previousCommit
Origin Master: $remoteHead

### Evidence Check

text
$($evidenceResults -join [Environment]::NewLine)

### Rollback Readiness Findings

text
$($readinessFindings -join [Environment]::NewLine)

### Dry-Run Decision

NO-GO

Production rollback remains blocked. This phase records rollback strategy and recovery drill readiness only.
"@

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::AppendAllText($auditPath, $append, $utf8NoBom)

Write-Output "PHASE28_ROLLBACK_RECOVERY_DRILL_DRY_RUN_PASS"