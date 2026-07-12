[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [string]$ExpectedBranch = 'chore/readiness-no-go-state',
    [string]$Remote = 'origin',
    [string]$BaseBranch = 'main',
    [string]$CommitMessage = 'record commercial readiness no-go state',
    [string]$ReadinessTrailer = 'ASOX-Readiness: commercial-no-go',
    [string]$PrTitle = 'Record commercial readiness NO-GO state',
    [switch]$OpenPr
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-Git {
    param(
        [Parameter(Mandatory)]
        [string[]]$Arguments,
        [switch]$AllowFailure
    )

    & git @Arguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0 -and -not $AllowFailure) {
        throw "git $($Arguments -join ' ') failed with exit code $exitCode."
    }

    return $exitCode
}

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
                $_.ToString().Trim()
            }
        } |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )
}

function Invoke-GovernanceValidateIsolated {
    param(
        [Parameter(Mandatory)]
        [string]$WorkingDirectory,
        [Parameter(Mandatory)]
        [string]$ScriptPath
    )

    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        throw "Governance script not found: $ScriptPath"
    }

    $validateCmd = @"
Set-Location -LiteralPath '$WorkingDirectory'
& '$ScriptPath' validate
exit `$LASTEXITCODE
"@

    $output = & powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command $validateCmd 2>&1
    $exitCode = $LASTEXITCODE

    if ($output) {
        $output | ForEach-Object { Write-Host $_ }
    }

    if ($exitCode -ne 0) {
        throw "Governance validation failed with exit code $exitCode."
    }
}

function Get-RemoteUrl {
    param(
        [Parameter(Mandatory)]
        [string]$RemoteName
    )

    return (Get-GitOutput -Arguments @('remote', 'get-url', $RemoteName))
}

function Get-PullRequestUrlFromRemote {
    param(
        [Parameter(Mandatory)]
        [string]$RemoteUrl,
        [Parameter(Mandatory)]
        [string]$BaseBranchName,
        [Parameter(Mandatory)]
        [string]$HeadBranchName
    )

    if ($RemoteUrl -match 'github\.com[:/](?<owner>[^/]+)/(?<repo>[^/.]+)(?:\.git)?$') {
        return "https://github.com/$($Matches['owner'])/$($Matches['repo'])/compare/$BaseBranchName...$HeadBranchName?expand=1"
    }

    return $null
}

function Get-CommitsAheadOfBase {
    param(
        [Parameter(Mandatory)]
        [string]$BaseRef
    )

    return Get-GitOutputLines -Arguments @('rev-list', "$BaseRef..HEAD")
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

Set-Location -LiteralPath $RepoRoot

$insideRepo = Get-GitOutput -Arguments @('rev-parse', '--is-inside-work-tree')
if ($insideRepo -ne 'true') {
    throw "Not a Git worktree: $RepoRoot"
}

$governanceScript = Join-Path $RepoRoot 'tools\governance.ps1'

Invoke-Git -Arguments @('fetch', '--prune', $Remote) | Out-Null

$currentBranch = Get-GitOutput -Arguments @('branch', '--show-current')
if ($currentBranch -ne $ExpectedBranch) {
    throw "Expected branch '$ExpectedBranch', but current branch is '$currentBranch'."
}

$head = Get-GitOutput -Arguments @('rev-parse', 'HEAD')
$actualMessage = Get-GitOutput -Arguments @('log', '-1', '--format=%s', 'HEAD')

& git merge-base --is-ancestor "$Remote/$BaseBranch" HEAD
if ($LASTEXITCODE -ne 0) {
    throw "HEAD is not based on the current $Remote/$BaseBranch."
}

$aheadCountText = Get-GitOutput -Arguments @('rev-list', '--count', "$Remote/$BaseBranch..HEAD")
if ([int]$aheadCountText -lt 1) {
    throw "Branch has no commits ahead of $Remote/$BaseBranch."
}

$aheadCommits = Get-CommitsAheadOfBase -BaseRef "$Remote/$BaseBranch"
$matchingCommits = @()

foreach ($commit in $aheadCommits) {
    if (Test-CommitHasTrailer -CommitSha $commit -TrailerLine $ReadinessTrailer) {
        $matchingCommits += $commit
    }
}

if ($matchingCommits.Count -eq 0) {
    throw "No readiness commit with trailer '$ReadinessTrailer' exists on this branch ahead of $Remote/$BaseBranch."
}

if ($matchingCommits.Count -gt 1) {
    throw "Multiple readiness commits with trailer '$ReadinessTrailer' exist on this branch ahead of $Remote/${BaseBranch}: $($matchingCommits -join ', ')"
}

$readinessCommit = $matchingCommits[0]
$readinessSubject = Get-GitOutput -Arguments @('log', '-1', '--format=%s', $readinessCommit)

if ($readinessSubject -ne $CommitMessage) {
    throw "Readiness commit '$readinessCommit' has subject '$readinessSubject', expected '$CommitMessage'."
}

Write-Host "Current HEAD: $head"
Write-Host "HEAD message: $actualMessage"
Write-Host "Readiness commit selected: $readinessCommit"
Write-Host "Readiness trailer: $ReadinessTrailer"

Invoke-Git -Arguments @('log', '--oneline', '--decorate', "$Remote/$BaseBranch..HEAD") | Out-Null
Invoke-Git -Arguments @('diff', '--name-status', "$Remote/$BaseBranch...HEAD") | Out-Null
Invoke-Git -Arguments @('diff', '--check', "$Remote/$BaseBranch...HEAD") | Out-Null
Invoke-GovernanceValidateIsolated -WorkingDirectory $RepoRoot -ScriptPath $governanceScript
Invoke-Git -Arguments @('status', '--short', '--branch') | Out-Null
Invoke-Git -Arguments @('push', '--set-upstream', $Remote, $ExpectedBranch) | Out-Null

$gh = Get-Command gh -ErrorAction SilentlyContinue
$prUrl = $null

if ($null -ne $gh) {
    & gh auth status *> $null
    if ($LASTEXITCODE -eq 0) {
        $existingPr = & gh pr list --head $ExpectedBranch --base $BaseBranch --state open --json url --jq '.[0].url'
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($existingPr)) {
            $prUrl = ($existingPr | Out-String).Trim()
            Write-Host "Existing PR: $prUrl"
        }
        else {
            $prBody = @"
## Purpose

Materialize and record the current commercial-readiness NO-GO decision.

## Validation

- Repository governance validation passes.
- The committed diff was checked for whitespace errors.
- Unrelated local evidence and log changes were not staged or committed.

## Traceability

- Readiness trailer: $ReadinessTrailer
"@

            $ghArgs = @(
                'pr', 'create',
                '--base', $BaseBranch,
                '--head', $ExpectedBranch,
                '--title', $PrTitle,
                '--body', $prBody
            )

            $createdPr = & gh @ghArgs
            if ($LASTEXITCODE -ne 0) {
                throw "Branch was pushed, but GitHub PR creation failed."
            }

            $prUrl = ($createdPr | Out-String).Trim()
            if (-not [string]::IsNullOrWhiteSpace($prUrl)) {
                Write-Host "Created PR: $prUrl"
            }
        }

        if ($OpenPr -and -not [string]::IsNullOrWhiteSpace($prUrl)) {
            & gh pr view --web
        }
    }
}

if ([string]::IsNullOrWhiteSpace($prUrl)) {
    $remoteUrl = Get-RemoteUrl -RemoteName $Remote
    $compareUrl = Get-PullRequestUrlFromRemote -RemoteUrl $remoteUrl -BaseBranchName $BaseBranch -HeadBranchName $ExpectedBranch
    if (-not [string]::IsNullOrWhiteSpace($compareUrl)) {
        Write-Host "Open this URL to create/review the PR: $compareUrl"
    }
}

Write-Host '[OK] Readiness branch validated and published without touching unrelated local changes.'
