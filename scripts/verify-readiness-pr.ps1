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
    [string]$ExpectedStashLabel = 'ASOX-Readiness: backup unrelated local logs and evidence before final run',
    [switch]$EmitJson
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

$statusLines = @(
    Get-GitOutputLines -Arguments @('status', '--short', '--branch')
)
$statusLineCount = @($statusLines).Count
Require ($statusLineCount -eq 1) "Working tree is not clean: $($statusLines -join ' | ')"

& git merge-base --is-ancestor "${Remote}/${BaseBranch}" HEAD
Require ($LASTEXITCODE -eq 0) "HEAD is not based on ${Remote}/${BaseBranch}."

$aheadCount = [int](Get-GitOutput -Arguments @('rev-list', '--count', "${Remote}/${BaseBranch}..HEAD"))
Require ($aheadCount -ge 1) "Branch has no commits ahead of ${Remote}/${BaseBranch}."

$aheadCommits = @(
    Get-GitOutputLines -Arguments @('rev-list', "${Remote}/${BaseBranch}..HEAD")
)
Require (@($aheadCommits).Count -ge 1) "No ahead commits were enumerated from ${Remote}/${BaseBranch}..HEAD."

$matchingCommits = @()
foreach ($commit in $aheadCommits) {
    if (Test-CommitHasTrailer -CommitSha $commit -TrailerLine $ReadinessTrailer) {
        $matchingCommits += $commit
    }
}

$matchingCommitCount = @($matchingCommits).Count
Require ($matchingCommitCount -eq 1) "Expected exactly one readiness commit with trailer '$ReadinessTrailer', found $matchingCommitCount."

$readinessCommit = $matchingCommits[0]
$readinessSubject = Get-GitOutput -Arguments @('log', '-1', '--format=%s', $readinessCommit)
Require ($readinessSubject -eq $ReadinessCommitMessage) "Readiness commit subject mismatch: '$readinessSubject'"

$stashLines = @(
    Get-GitOutputLines -Arguments @('stash', 'list')
)
$stashMatch = @(
    foreach ($line in $stashLines) {
        if ($line -match [regex]::Escape($ExpectedStashLabel)) {
            $line
        }
    }
)
$stashMatchCount = @($stashMatch).Count
Require ($stashMatchCount -ge 1) "Expected stash label not found: $ExpectedStashLabel"

$ghVersionOutput = & gh --version 2>$null
Require ($LASTEXITCODE -eq 0) 'GitHub CLI is not available on PATH.'

$authStatusOutput = & gh auth status 2>&1
Require ($LASTEXITCODE -eq 0) "GitHub CLI is not authenticated. Output: $($authStatusOutput | Out-String).Trim()"

$prJson = & gh pr view $ExpectedPrNumber --json number,title,state,headRefName,baseRefName,url 2>&1
Require ($LASTEXITCODE -eq 0) "Unable to query PR #$ExpectedPrNumber. Output: $($prJson | Out-String).Trim()"

$pr = $prJson | ConvertFrom-Json

Require ([int]$pr.number -eq $ExpectedPrNumber) "PR number mismatch. Got $($pr.number)"
Require ($pr.title -eq $ExpectedPrTitle) "PR title mismatch. Got '$($pr.title)'"
Require ($pr.state -eq 'OPEN') "PR #$ExpectedPrNumber is not OPEN. State: $($pr.state)"
Require ($pr.headRefName -eq $ExpectedBranch) "PR head branch mismatch. Got '$($pr.headRefName)'"
Require ($pr.baseRefName -eq $BaseBranch) "PR base branch mismatch. Got '$($pr.baseRefName)'"

$result = [ordered]@{
    repoRoot = $RepoRoot
    branch = $currentBranch
    head = $head
    remote = $Remote
    baseBranch = $BaseBranch
    aheadCount = $aheadCount
    readinessCommit = $readinessCommit
    readinessCommitSubject = $readinessSubject
    readinessTrailer = $ReadinessTrailer
    stashMatchCount = $stashMatchCount
    stashLabel = $ExpectedStashLabel
    prNumber = [int]$pr.number
    prTitle = $pr.title
    prState = $pr.state
    prUrl = $pr.url
    verifiedAtUtc = [DateTime]::UtcNow.ToString('o')
    pass = $true
}

if ($EmitJson) {
    $result | ConvertTo-Json -Depth 8
    exit 0
}

Write-Host "[PASS] Branch: $($result.branch)"
Write-Host "[PASS] HEAD: $($result.head)"
Write-Host "[PASS] Readiness commit: $($result.readinessCommit)"
Write-Host "[PASS] PR #$($result.prNumber): $($result.prTitle) [$($result.prState)]"
Write-Host "[PASS] Stash matches: $($result.stashMatchCount)"
Write-Host "[PASS] Verified at UTC: $($result.verifiedAtUtc)"
Write-Host '[PASS] Readiness PR state is valid, published, clean, and recoverable.'
