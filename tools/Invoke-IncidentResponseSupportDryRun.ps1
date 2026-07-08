param()

$ErrorActionPreference = "Stop"

$repo = (Get-Location).ProviderPath
[System.Environment]::CurrentDirectory = $repo

$auditPath = 'E:\saead\ssl\s43_refactor\AUDIT\PHASE29_INCIDENT_RESPONSE_ESCALATION_AND_SUPPORT_RUNBOOK_DRY_RUN_20260616_100046.md'

Write-Output "PHASE29_INCIDENT_RESPONSE_SUPPORT_DRY_RUN_START"

$gitStatus = git status --porcelain
$branchStatus = git status -sb
$head = git rev-parse --short HEAD
$remoteHead = git rev-parse --short origin/master

$evidencePatterns = @(
    "AUDIT/PHASE26_*",
    "AUDIT/PHASE27_*",
    "AUDIT/PHASE28_*",
    "AUDIT/PHASE25_ARTIFACT_MANIFEST_DRY_RUN.txt",
    "AUDIT/PHASE25_ARTIFACT_SHA256_DRY_RUN.txt",
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
    $readinessFindings.Add("PASS: Working tree is clean before Phase 29 artifact creation.")
} else {
    $readinessFindings.Add("INFO: Working tree has pending Phase 29 files or other changes.")
}

if ($head -eq $remoteHead) {
    $readinessFindings.Add("PASS: Local HEAD matches origin/master.")
} else {
    $readinessFindings.Add("BLOCKED: Local HEAD does not match origin/master.")
}

$readinessFindings.Add("INFO: Current HEAD is $head.")
$readinessFindings.Add("INFO: Severity model is documented as SEV1 through SEV4.")
$readinessFindings.Add("BLOCKED: Live incident simulation remains blocked.")
$readinessFindings.Add("BLOCKED: Production deployment remains blocked.")
$readinessFindings.Add("BLOCKED: Production rollback remains blocked.")
$readinessFindings.Add("BLOCKED: Incident owner and escalation backup are not assigned in this dry-run.")
$readinessFindings.Add("BLOCKED: Customer/support communication channel is not activated in this dry-run.")
$readinessFindings.Add("BLOCKED: Post-incident review owner is not assigned in this dry-run.")
$readinessFindings.Add("INFO: No deployment, rollback, tag mutation, secret mutation, or remote setting change was performed.")

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

### Incident Response Readiness Findings

text
$($readinessFindings -join [Environment]::NewLine)

### Dry-Run Decision

NO-GO

Production release and live incident simulation remain blocked. This phase records incident response, escalation, and support readiness only.
"@

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::AppendAllText($auditPath, $append, $utf8NoBom)

Write-Output "PHASE29_INCIDENT_RESPONSE_SUPPORT_DRY_RUN_PASS"