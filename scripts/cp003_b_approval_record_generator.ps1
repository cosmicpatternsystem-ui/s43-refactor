param(
    [Parameter(Mandatory = $true)]
    [string]$RequestId,

    [Parameter(Mandatory = $true)]
    [string]$RequestingParty,

    [Parameter(Mandatory = $true)]
    [string]$ReviewingParty,

    [Parameter(Mandatory = $false)]
    [string]$TargetBranch = "cp003-b-integration-planning",

    [Parameter(Mandatory = $false)]
    [ValidateSet(
        "APPROVED_FOR_GOVERNANCE_ONLY",
        "APPROVED_FOR_SINGLE_POINT_IMPLEMENTATION_REVIEW",
        "REJECTED",
        "DEFERRED"
    )]
    [string]$Decision = "DEFERRED"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$templatePath = Join-Path $PSScriptRoot "..\governance\CP003_B_APPROVAL_GATE_TEMPLATE.md"
$outputDir = Join-Path $PSScriptRoot "..\governance\approval_records"

if (-not (Test-Path $templatePath)) {
    throw "Template not found: $templatePath"
}

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

$timestampUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$dateStamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")

$branch = $TargetBranch
try {
    $gitBranch = git rev-parse --abbrev-ref HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and $gitBranch) {
        $branch = $gitBranch.Trim()
    }
} catch {}

$commit = "UNKNOWN"
try {
    $gitCommit = git rev-parse --short HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and $gitCommit) {
        $commit = $gitCommit.Trim()
    }
} catch {}

$safeRequestId = ($RequestId -replace '[^A-Za-z0-9._-]', '_')
$outputName = "CP003_B_APPROVAL_RECORD_${safeRequestId}_${dateStamp}.md"
$outputPath = Join-Path $outputDir $outputName

if (Test-Path $outputPath) {
    throw "Approval record already exists: $outputPath"
}

$templateContent = Get-Content $templatePath -Raw

$record = @"
# CP003-B Approval Record

## Record Metadata

- Approval record title: CP003-B Approval Record - $RequestId
- Approval record version: v1
- Requesting party: $RequestingParty
- Reviewing party: $ReviewingParty
- Approval decision: $Decision
- Approval timestamp: $timestampUtc
- Target branch: $branch
- Governing baseline tag: s43-cp003-a-locked
- Source template: CP003_B_APPROVAL_GATE_TEMPLATE.md
- Source commit: $commit

## Request Scope

- Target file: REQUIRED
- Target function or insertion point: REQUIRED
- Exact mutation summary: REQUIRED
- Expected Git diff footprint: REQUIRED
- Expected new imports: NONE or REQUIRED
- Expected new dependencies: NONE or REQUIRED
- Expected runtime behavior: REQUIRED
- Expected failure behavior: REQUIRED
- Expected deny-by-default behavior: REQUIRED
- Expected audit or logging behavior: REQUIRED

## Safety Controls

- Expected rollback command sequence: REQUIRED
- Expected verification command sequence: REQUIRED
- Expected test command sequence: REQUIRED
- Explicit live trading ruling: UNAUTHORIZED unless explicitly and separately approved
- Explicit broker connectivity ruling: UNAUTHORIZED unless explicitly and separately approved
- Explicit environment activation ruling: UNAUTHORIZED unless explicitly and separately approved
- Explicit order placement ruling: UNAUTHORIZED unless explicitly and separately approved

## Reviewer Notes

- Governance notes: REQUIRED
- Evidence references: REQUIRED
- Additional constraints: REQUIRED

## Template Reference

$templateContent
"@

Set-Content -Path $outputPath -Value $record -Encoding UTF8

Write-Host "Approval record created:"
Write-Host $outputPath
