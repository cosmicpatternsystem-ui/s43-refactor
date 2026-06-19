param()

$ErrorActionPreference = "Stop"

$repo = (Get-Location).ProviderPath
[System.Environment]::CurrentDirectory = $repo

$auditPath = 'E:\saead\ssl\s43_refactor\AUDIT\PHASE30_RELEASE_APPROVAL_GOVERNANCE_AND_SIGNOFF_MATRIX_DRY_RUN_20260616_101037.md'

Write-Output "PHASE30_RELEASE_APPROVAL_GOVERNANCE_DRY_RUN_START"

$gitStatus = git status --porcelain
$branchStatus = git status -sb
$head = git rev-parse --short HEAD
$remoteHead = git rev-parse --short origin/master

$evidencePatterns = @(
    "AUDIT/COMMERCIAL_MANDATORY_ROADMAP.md",
    "AUDIT/PHASE22_*",
    "AUDIT/PHASE23_*",
    "AUDIT/PHASE24_*",
    "AUDIT/PHASE25_*",
    "AUDIT/PHASE26_*",
    "AUDIT/PHASE27_*",
    "AUDIT/PHASE28_*",
    "AUDIT/PHASE29_*",
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
    $readinessFindings.Add("PASS: Working tree is clean before Phase 30 artifact creation.")
} else {
    $readinessFindings.Add("INFO: Working tree has pending Phase 30 files or other changes.")
}

if ($head -eq $remoteHead) {
    $readinessFindings.Add("PASS: Local HEAD matches origin/master.")
} else {
    $readinessFindings.Add("BLOCKED: Local HEAD does not match origin/master.")
}

$readinessFindings.Add("INFO: Current HEAD is $head.")
$readinessFindings.Add("INFO: Approval roles are defined for release owner, engineering, QA, security, operations, and business.")
$readinessFindings.Add("BLOCKED: Real release approval is not granted in this dry-run.")
$readinessFindings.Add("BLOCKED: Mandatory approvers are not assigned in this dry-run.")
$readinessFindings.Add("BLOCKED: Final auditable sign-off record is not created in this dry-run.")
$readinessFindings.Add("BLOCKED: Production deployment remains blocked.")
$readinessFindings.Add("BLOCKED: Production rollback remains blocked.")
$readinessFindings.Add("INFO: No deployment, tag mutation, rollback execution, secret mutation, or remote setting change was performed.")

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

### Approval Governance Readiness Findings

text
$($readinessFindings -join [Environment]::NewLine)

### Dry-Run Decision

NO-GO

Real release remains blocked. This phase records release approval governance and sign-off readiness only.
"@

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::AppendAllText($auditPath, $append, $utf8NoBom)

Write-Output "PHASE30_RELEASE_APPROVAL_GOVERNANCE_DRY_RUN_PASS"