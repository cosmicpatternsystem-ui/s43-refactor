[CmdletBinding()]
param(
    [string]$BranchName = "governance/canonical-roadmap-reference",
    [string]$BaseBranch = "main",
    [string]$RemoteName = "origin",
    [switch]$SkipValidation
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Step {
    param([Parameter(Mandatory = $true)][string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([Parameter(Mandatory = $true)][string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([Parameter(Mandatory = $true)][string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Fail {
    param([Parameter(Mandatory = $true)][string]$Message)
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [switch]$AllowNonZeroExit
    )

    $output = & git @Arguments 2>&1
    $exitCode = $LASTEXITCODE

    if (-not $AllowNonZeroExit -and $exitCode -ne 0) {
        $rendered = $Arguments -join ' '
        $text = (($output | ForEach-Object { "$_" }) -join [Environment]::NewLine).Trim()

        if ([string]::IsNullOrWhiteSpace($text)) {
            throw "git $rendered failed with exit code $exitCode."
        }

        throw "git $rendered failed with exit code $exitCode.`n$text"
    }

    return [pscustomobject]@{
        ExitCode = $exitCode
        Output   = @($output)
        Text     = (($output | ForEach-Object { "$_" }) -join [Environment]::NewLine)
    }
}

function Assert-InsideGitRepo {
    $result = Invoke-Git -Arguments @("rev-parse", "--is-inside-work-tree")
    $value = $result.Text.Trim()

    if ($value -ne "true") {
        throw "Current directory is not inside a git work tree."
    }

    Write-Ok "Inside a git repository."
}

function Get-RepoRoot {
    $result = Invoke-Git -Arguments @("rev-parse", "--show-toplevel")
    $root = $result.Text.Trim()

    if ([string]::IsNullOrWhiteSpace($root)) {
        throw "Unable to resolve repository root."
    }

    return $root
}

function Push-RepoLocation {
    $resolvedRepoRoot = Get-RepoRoot
    Push-Location -LiteralPath $resolvedRepoRoot
    return $resolvedRepoRoot
}

function Get-StatusPorcelainText {
    $result = Invoke-Git -Arguments @("status", "--porcelain=v1", "--untracked-files=all")
    return (($result.Text -replace "`r", "").Trim())
}

function Assert-CleanWorktree {
    $statusText = Get-StatusPorcelainText

    if ([string]::IsNullOrWhiteSpace($statusText)) {
        Write-Ok "Working tree is clean."
        return
    }

    Write-Warn "Working tree is not clean. Current git status:"
    foreach ($line in ($statusText -split "`n")) {
        $trimmed = $line.TrimEnd()
        if (-not [string]::IsNullOrWhiteSpace($trimmed)) {
            Write-Host "  $trimmed" -ForegroundColor Yellow
        }
    }

    throw "Working tree is not clean. Commit, stash, or remove pending changes before continuing."
}

function Test-LocalBranchExists {
    param([Parameter(Mandatory = $true)][string]$Name)

    $result = Invoke-Git -Arguments @("show-ref", "--verify", "--quiet", "refs/heads/$Name") -AllowNonZeroExit
    return ($result.ExitCode -eq 0)
}

function Test-RemoteBranchExists {
    param(
        [Parameter(Mandatory = $true)][string]$Remote,
        [Parameter(Mandatory = $true)][string]$Name
    )

    $result = Invoke-Git -Arguments @("ls-remote", "--exit-code", "--heads", $Remote, $Name) -AllowNonZeroExit
    return ($result.ExitCode -eq 0)
}

function Fetch-Prune {
    param([Parameter(Mandatory = $true)][string]$Remote)

    $result = Invoke-Git -Arguments @("fetch", $Remote, "--prune")
    foreach ($line in $result.Output) {
        $text = [string]$line
        if (-not [string]::IsNullOrWhiteSpace($text)) {
            Write-Host $text
        }
    }

    Write-Ok "Fetched latest refs from $Remote and pruned stale tracking refs."
}

function Checkout-BaseBranch {
    param([Parameter(Mandatory = $true)][string]$Name)

    $result = Invoke-Git -Arguments @("checkout", $Name)
    foreach ($line in $result.Output) {
        $text = [string]$line
        if (-not [string]::IsNullOrWhiteSpace($text)) {
            Write-Host $text
        }
    }

    Write-Ok "Checked out $Name."
}

function Pull-BaseBranch {
    param(
        [Parameter(Mandatory = $true)][string]$Remote,
        [Parameter(Mandatory = $true)][string]$Name
    )

    $result = Invoke-Git -Arguments @("pull", "--ff-only", $Remote, $Name)
    foreach ($line in $result.Output) {
        $text = [string]$line
        if (-not [string]::IsNullOrWhiteSpace($text)) {
            Write-Host $text
        }
    }

    Write-Ok "$Name is synchronized with $Remote/$Name."
}

function Delete-LocalBranchIfPresent {
    param([Parameter(Mandatory = $true)][string]$Name)

    if (Test-LocalBranchExists -Name $Name) {
        $result = Invoke-Git -Arguments @("branch", "-d", $Name)
        foreach ($line in $result.Output) {
            $text = [string]$line
            if (-not [string]::IsNullOrWhiteSpace($text)) {
                Write-Host $text
            }
        }

        Write-Ok "Deleted local branch $Name."
    }
    else {
        Write-Warn "Local branch $Name does not exist; skipping."
    }
}

function Delete-RemoteBranchIfPresent {
    param(
        [Parameter(Mandatory = $true)][string]$Remote,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if (Test-RemoteBranchExists -Remote $Remote -Name $Name) {
        $result = Invoke-Git -Arguments @("push", $Remote, "--delete", $Name)
        foreach ($line in $result.Output) {
            $text = [string]$line
            if (-not [string]::IsNullOrWhiteSpace($text)) {
                Write-Host $text
            }
        }

        Write-Ok "Deleted remote branch $Remote/$Name."
    }
    else {
        Write-Warn "Remote branch $Remote/$Name does not exist; skipping."
    }
}

function Assert-RemoteTrackingRefAbsent {
    param(
        [Parameter(Mandatory = $true)][string]$Remote,
        [Parameter(Mandatory = $true)][string]$Name
    )

    $result = Invoke-Git -Arguments @("branch", "-r", "--list", "$Remote/$Name")
    $text = $result.Text.Trim()

    if ([string]::IsNullOrWhiteSpace($text)) {
        Write-Ok "Remote-tracking ref $Remote/$Name is absent."
        return
    }

    throw "Remote-tracking ref still present: $Remote/$Name"
}

function Invoke-RepositoryScript {
    param(
        [Parameter(Mandatory = $true)][string]$RelativePath,
        [Parameter(Mandatory = $true)][string]$FailureMessage
    )

    $scriptPath = Join-Path (Get-RepoRoot) $RelativePath

    if (-not (Test-Path -LiteralPath $scriptPath)) {
        throw "Required script not found: $RelativePath"
    }

    Write-Host "PS> pwsh $RelativePath" -ForegroundColor DarkGray
    & pwsh -NoLogo -NoProfile -File $scriptPath

    if ($LASTEXITCODE -ne 0) {
        throw $FailureMessage
    }
}

function Invoke-ValidationSuite {
    Write-Step "Run governance validation suite"

    Invoke-RepositoryScript `
        -RelativePath "scripts/validate-roadmap-authority.ps1" `
        -FailureMessage "validate-roadmap-authority.ps1 failed."
    Write-Ok "Roadmap authority validation passed."

    Invoke-RepositoryScript `
        -RelativePath "scripts/validate-roadmap.ps1" `
        -FailureMessage "validate-roadmap.ps1 failed."
    Write-Ok "Roadmap schema validation passed."

    Invoke-RepositoryScript `
        -RelativePath "scripts/test-roadmap.ps1" `
        -FailureMessage "test-roadmap.ps1 failed."
    Write-Ok "Roadmap smoke tests passed."
}

$repoRoot = $null

try {
    Write-Step "Validate repository context"
    Assert-InsideGitRepo

    $repoRoot = Push-RepoLocation
    Write-Ok "Repository root: $repoRoot"

    Write-Step "Fetch latest refs"
    Fetch-Prune -Remote $RemoteName

    Write-Step "Assert clean worktree before cleanup"
    Assert-CleanWorktree

    Write-Step "Checkout base branch"
    Checkout-BaseBranch -Name $BaseBranch

    Write-Step "Fast-forward local base branch"
    Pull-BaseBranch -Remote $RemoteName -Name $BaseBranch

    Write-Step "Delete local feature branch if present"
    Delete-LocalBranchIfPresent -Name $BranchName

    Write-Step "Delete remote feature branch if present"
    Delete-RemoteBranchIfPresent -Remote $RemoteName -Name $BranchName

    Write-Step "Prune remote-tracking refs"
    Fetch-Prune -Remote $RemoteName

    Write-Step "Verify remote-tracking ref removal"
    Assert-RemoteTrackingRefAbsent -Remote $RemoteName -Name $BranchName

    Write-Step "Assert clean worktree after cleanup"
    Assert-CleanWorktree

    if (-not $SkipValidation) {
        Invoke-ValidationSuite
    }
    else {
        Write-Warn "Validation suite skipped by request."
    }

    Write-Step "Final summary"
    Write-Host "Repository cleanup completed successfully." -ForegroundColor Green
    Write-Host "Base branch  : $BaseBranch"
    Write-Host "Remote       : $RemoteName"
    Write-Host "Closed branch: $BranchName"
    Write-Host "Validation   : $(if ($SkipValidation) { 'SKIPPED' } else { 'PASSED' })"
    Write-Host ""
    Write-Host "Final state:" -ForegroundColor Green
    Write-Host "  - Repository synced with $RemoteName/$BaseBranch"
    Write-Host "  - Feature branch removed locally if present"
    Write-Host "  - Feature branch removed remotely if present"
    Write-Host "  - Remote-tracking refs pruned"
    Write-Host "  - Worktree confirmed clean"
    Write-Host "  - Governance cleanup complete"

    exit 0
}
catch {
    Write-Fail $_.Exception.Message
    exit 1
}
finally {
    if ($null -ne $repoRoot) {
        Pop-Location
    }
}