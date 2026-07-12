[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [string]$ExpectedBranch = 'chore/readiness-no-go-state',
    [string]$Remote = 'origin',
    [string]$BaseBranch = 'main',
    [string]$ReadinessCommitMessage = 'record commercial readiness no-go state',
    [string]$ReadinessTrailer = 'ASOX-Readiness: commercial-no-go',
    [int]$ExpectedPrNumber = 282,
    [string]$ExpectedPrTitle = 'Record commercial readiness NO-GO state',
    [string]$ExpectedStashLabel = 'ASOX-Readiness: backup unrelated local logs and evidence before final run'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Get-GitOutput {
    param(
        [Parameter(Mandatory)]
        [string[]]$Arguments
    )

    $output = & git @Arguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "git $($Arguments -join ' ') failed with exit code $exitCode."
    }

    if ($null -eq $output) {
        return ''
    }

    return ($output | Out-String).Trim()
}

function Get-GitOutputLines {
    param(
        [Parameter(Mandatory)]
        [string[]]$Arguments
    )

    $output = & git @Arguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "git $($Arguments -join ' ') failed with exit code $exitCode."
    }

    if ($null -eq $output) {
        return @()
    }

    return @(
        $output |
        ForEach-Object {
            if ($null -ne $_) {
                $_.ToString().TrimEnd()
            }
        } |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )
}

function Test-CommitHasTrailer {
    param(
        [Parameter(Mandatory)]
        [string]$CommitSha,
        [Parameter(Mandatory)]
        [string]$TrailerLine
    )

    $body = Get-GitOutput -Arguments @('show', '-s', '--format=%B', $CommitSha)
    $lines = @($body -split "`r?`n")

    foreach ($line in $lines) {
        if ($line.Trim() -ceq $TrailerLine) {
            return $true
        }
    }

    return $false
}

function Require {
    param(
        [Parameter(Mandatory)]
        [bool]$Condition,
        [Parameter(Mandatory)]
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

Set-Location -LiteralPath $RepoRoot

$insideRepo = Get-GitOutput -Arguments @('rev-parse', '--is-inside-work-tree')
Require ($insideRepo -eq 'true') "Not inside a Git worktree: $RepoRoot"

$currentBranch = Get-GitOutput -Arguments @('branch', '--show-current')
Require ($currentBranch -eq $ExpectedBranch) "Expected branch '$ExpectedBranch', but current branch is '$currentBranch'."

$head = Get-GitOutput -Arguments @('rev-parse', 'HEAD')
$statusLines = Get-GitOutputLines -Arguments @('status', '--short', '--branch')
Require ($statusLines.Count -eq 1) "Working tree is not clean: $($statusLines -join ' | ')"

& git merge-base --is-ancestor "${Remote}/${BaseBranch}" HEAD
Require ($LASTEXITCODE -eq 0) "HEAD is not based on ${Remote}/${BaseBranch}."

$aheadCount = [int](Get-GitOutput -Arguments @('rev-list', '--count', "${Remote}/${BaseBranch}..HEAD"))
Require ($aheadCount -ge 1) "Branch has no commits ahead of ${Remote}/${BaseBranch}."

$aheadCommits = Get-GitOutputLines -Arguments @('rev-list', "${Remote}/${BaseBranch}..HEAD")
$matchingCommits = @()

foreach ($commit in $aheadCommits) {
    if (Test-CommitHasTrailer -CommitSha $commit -TrailerLine $ReadinessTrailer) {
        $matchingCommits += $commit
    }
}

Require ($matchingCommits.Count -eq 1) "Expected exactly one readiness commit with trailer '$ReadinessTrailer', found $($matchingCommits.Count)."

$readinessCommit = $matchingCommits[0]
$readinessSubject = Get-GitOutput -Arguments @('log', '-1', '--format=%s', $readinessCommit)
Require ($readinessSubject -eq $ReadinessCommitMessage) "Readiness commit subject mismatch: '$readinessSubject'"

$stashLines = Get-GitOutputLines -Arguments @('stash', 'list')
$stashMatch = $stashLines | Where-Object { $_ -match [regex]::Escape($ExpectedStashLabel) }
Require ($stashMatch.Count -ge 1) "Expected stash label not found: $ExpectedStashLabel"

$gh = Get-Command gh -ErrorAction SilentlyContinue
Require ($null -ne $gh) "GitHub CLI 'gh' is not available."

& gh auth status *> $null
Require ($LASTEXITCODE -eq 0) "GitHub CLI is not authenticated."

$prJson = & gh pr view $ExpectedPrNumber --json number,title,state,headRefName,baseRefName,url
Require ($LASTEXITCODE -eq 0) "Failed to read PR #$ExpectedPrNumber."

$pr = $prJson | ConvertFrom-Json

Require ($pr.number -eq $ExpectedPrNumber) "PR number mismatch."
Require ($pr.title -eq $ExpectedPrTitle) "PR title mismatch: '$($pr.title)'"
Require ($pr.state -eq 'OPEN') "PR is not OPEN."
Require ($pr.headRefName -eq $ExpectedBranch) "PR head branch mismatch: '$($pr.headRefName)'"
Require ($pr.baseRefName -eq $BaseBranch) "PR base branch mismatch: '$($pr.baseRefName)'"

Write-Host "Branch: $currentBranch"
Write-Host "HEAD: $head"
Write-Host "Readiness commit: $readinessCommit"
Write-Host "Readiness trailer: $ReadinessTrailer"
Write-Host "Ahead of ${Remote}/${BaseBranch}: $aheadCount commit(s)"
Write-Host "PR: #$($pr.number) $($pr.title)"
Write-Host "PR URL: $($pr.url)"
Write-Host "Stash preserved: $($stashMatch[0])"
Write-Host '[PASS] Readiness PR state is valid, published, clean, and recoverable.'
