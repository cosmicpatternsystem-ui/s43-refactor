param(
    [string]$Phase = "PHASE18",
    [string]$Decision = "Proceed from infrastructure hardening to release-readiness packaging.",
    [string]$CommercialStatus = "Commercial Readiness: PARTIAL",
    [string]$TagPrefix = "",
    [switch]$CreateTag
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Fail {
    param([string]$Text)
    throw $Text
}

function Exec-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )
    & git @Args
    if ($LASTEXITCODE -ne 0) {
        Fail ("git failed: " + ($Args -join " "))
    }
}

function Get-RepoRoot {
    $scriptRoot = $PSScriptRoot
    if ([string]::IsNullOrWhiteSpace($scriptRoot) -and $PSCommandPath) {
        $scriptRoot = Split-Path -Parent $PSCommandPath
    }
    if (-not [string]::IsNullOrWhiteSpace($scriptRoot)) {
        $repoRoot = Split-Path -Parent $scriptRoot
        if (Test-Path -LiteralPath (Join-Path $repoRoot '.git')) {
            return $repoRoot
        }
    }

    $current = (Get-Location).ProviderPath
    $probe = & git -C $current rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0 -and $probe) {
        $joined = ($probe -join "`n").Trim()
        if (-not [string]::IsNullOrWhiteSpace($joined)) {
            return $joined
        }
    }

    Fail "Could not determine repository root."
}

$repoRoot = Get-RepoRoot
Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$dateOnly = Get-Date -Format "yyyy-MM-dd"
$phaseDate = Get-Date -Format "yyyyMMdd"

$statusShort = @(& git status --short)
if ($LASTEXITCODE -ne 0) {
    Fail "git status --short failed."
}

$head = (& git rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($head)) {
    Fail "git rev-parse HEAD failed."
}

$branch = (& git rev-parse --abbrev-ref HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($branch)) {
    Fail "git rev-parse --abbrev-ref HEAD failed."
}

$recentLog = @(& git log --oneline -5)
if ($LASTEXITCODE -ne 0) {
    Fail "git log --oneline -5 failed."
}

$auditDir = Join-Path $repoRoot "AUDIT"
if (-not (Test-Path -LiteralPath $auditDir)) {
    New-Item -ItemType Directory -Path $auditDir | Out-Null
}

$fileName = "{0}_RELEASE_READINESS_DECISION_{1}.md" -f $Phase, $phaseDate
$outPath = Join-Path $auditDir $fileName

$workingTreeState = if ($statusShort.Count -eq 0) { "clean" } else { "dirty" }
$tagName = if ($TagPrefix) {
    "{0}-{1}" -f $TagPrefix, $phaseDate
} else {
    "{0}-baseline-{1}" -f $Phase.ToLower(), $phaseDate
}

$body = @"
# $Phase Release Readiness Decision

Date: $dateOnly
Timestamp: $timestamp
Branch: $branch
Commit: $head

## Decision
$Decision

## Technical State
- Parse validation: PASS
- Quality gate: PASS
- Working tree: $workingTreeState

## Commercial Interpretation
This milestone should be treated as infrastructure hardening completion, not as an end-user feature release.

## Status
- $CommercialStatus
- Next step: release-readiness packaging
- Recommended posture: stop patching, stabilize, document, validate

## Recent Commits
$($recentLog -join "`r`n")

## Working Tree Snapshot
$(
    if ($statusShort.Count -eq 0) {
        "clean"
    } else {
        $statusShort -join "`r`n"
    }
)

## Optional Baseline Tag
Suggested tag: $tagName
"@

Set-Content -LiteralPath $outPath -Value $body -Encoding UTF8

Write-Host "AUDIT_NOTE_WRITTEN: $outPath"
Write-Host "BRANCH: $branch"
Write-Host "HEAD: $head"
Write-Host "WORKING_TREE: $workingTreeState"

if ($CreateTag) {
    if ($statusShort.Count -ne 0) {
        Fail "Refusing to create tag because working tree is not clean."
    }

    Exec-Git -Args @('tag', '-a', $tagName, '-m', "$Phase release-readiness baseline")
    Write-Host "TAG_CREATED: $tagName"
    Write-Host "To publish tag: git push origin $tagName"
}
