[CmdletBinding()]
param(
    [string]$ExpectedBranch = "phase17-work-from-restore"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $RepoRoot

$RequiredPaths = @(
    "tools/phase17_approved_sync.ps1",
    "tools/phase18_approved_sync_wrapper.ps1",
    "ROADMAP/PHASE18_COMMERCIAL_RELEASE_CANDIDATE_PLAN_20260614.md",
    "AUDIT/PHASE18_RELEASE_READINESS_CHECKLIST_20260614.md",
    "AUDIT/PHASE18_RISK_REGISTER_20260614.md",
    "AUDIT/PHASE18_ONE_COPY_PASTE_AUTOMATION_STANDARD_20260614.md",
    "AUDIT/PHASE18_OPENING_AUTOMATION_VERIFICATION_20260614.md",
    "AUDIT/PHASE18_COMMERCIAL_RC_HARDENING_CONTROL_REGISTER_20260615.md"
)

$CurrentBranch = (git branch --show-current).Trim()
if ($CurrentBranch -ne $ExpectedBranch) {
    throw "Invalid branch: $CurrentBranch"
}

git fetch origin $ExpectedBranch | Out-Null

$Head = (git rev-parse HEAD).Trim()
$Origin = (git rev-parse "origin/$ExpectedBranch").Trim()
if ($Head -ne $Origin) {
    throw "HEAD and origin differ. HEAD=$Head ORIGIN=$Origin"
}

$Status = @(git status --short)
if ($Status.Count -gt 0) {
    throw ("Working tree is not clean: " + ($Status -join " | "))
}

$Missing = @()
foreach ($Path in $RequiredPaths) {
    if (-not (Test-Path -LiteralPath $Path)) {
        $Missing += $Path
    }
}

if ($Missing.Count -gt 0) {
    throw ("Missing required Phase 18 files: " + ($Missing -join " | "))
}

$LatestSubject = (git log -1 --pretty=%s).Trim()

Write-Host "PHASE18_PREFLIGHT_AUDIT_PASS"
Write-Host "BRANCH=$CurrentBranch"
Write-Host "HEAD=$Head"
Write-Host "ORIGIN=$Origin"
Write-Host "LATEST_SUBJECT=$LatestSubject"
Write-Host "REQUIRED_FILES_PRESENT=$($RequiredPaths.Count)"
Write-Host "WORKING_TREE=CLEAN"
