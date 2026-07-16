[CmdletBinding()]
param(
    [string]$RepoPath = "G:\s43_work\s43_g11_work",
    [string]$BaseBranch = "main",
    [string]$RemoteName = "origin",
    [string]$FinalBranch = "chore/pr-304-governance-closeout-final",
    [string]$ArtifactPath = "artifacts/governance-closeout/PR_FINALIZATION_STATUS.md",
    [ValidateSet("ignore","stash","commit")]
    [string]$JournalPolicy = "ignore",
    [string[]]$AllowedWorkingTreePaths = @(
        "scripts/verify-governance-closeout.ps1"
    ),
    [string]$JournalCommitMessage = "chore(journal): record journal entries (auto)"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$CandidateScripts = @(
    ".github/scripts/governance-guard.ps1",
    "scripts/verify-governance-closeout.ps1",
    "scripts/validate-roadmap-authority.ps1",
    "scripts/validate-roadmap.ps1",
    "scripts/test-roadmap.ps1",
    "scripts/verify-roadmap-smoke.ps1"
)

$HasDirtyJournal = $false
$JournalAction = "none"
$JournalCommitSha = $null
$JournalAheadBy = 0
$IsAllowedDivergence = $false

function Invoke-GitSafe {
    param([Parameter(Mandatory = $true)][string[]]$Args)

    $oldEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & git @Args 2>&1
        $code = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $oldEap
    }

    $text = ($output | ForEach-Object { $_.ToString() }) -join "`n"
    if ($code -ne 0) {
        throw "git $($Args -join ' ') failed with exit code $code.`n$text"
    }

    return $text.Trim()
}

function Normalize-RepoPath {
    param([Parameter(Mandatory = $true)][string]$PathValue)
    return ($PathValue -replace "\\","/").Trim()
}

function New-ResultObject {
    param(
        [Parameter(Mandatory = $true)][string]$Script,
        [Parameter(Mandatory = $true)][string]$Status,
        [AllowNull()][int]$ExitCode,
        [AllowNull()][string]$Notes
    )

    [pscustomobject]@{
        Script   = $Script
        Status   = $Status
        ExitCode = $ExitCode
        Notes    = $Notes
    }
}

function Invoke-OptionalPwshScript {
    param([Parameter(Mandatory = $true)][string]$ScriptPath)

    if (-not (Test-Path $ScriptPath)) {
        Write-Host "SKIPPED missing script: $ScriptPath" -ForegroundColor DarkYellow
        return (New-ResultObject -Script $ScriptPath -Status "SKIPPED_MISSING" -ExitCode $null -Notes "Script file not found")
    }

    Write-Host "RUNNING: $ScriptPath" -ForegroundColor Cyan

    $oldEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $captured = @()
    $code = $null

    try {
        $captured = & pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $ScriptPath 2>&1
        $code = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $oldEap
    }

    if ($captured) {
        foreach ($line in $captured) {
            Write-Host ($line.ToString())
        }
    }

    if ($code -eq 0) {
        Write-Host "PASSED: $ScriptPath" -ForegroundColor Green
        return (New-ResultObject -Script $ScriptPath -Status "PASSED" -ExitCode $code -Notes $null)
    }

    Write-Host "FAILED: $ScriptPath with exit code $code" -ForegroundColor Red
    return (New-ResultObject -Script $ScriptPath -Status "FAILED" -ExitCode $code -Notes "Non-zero exit code")
}

function Assert-ResultShape {
    param([Parameter(Mandatory = $true)][object]$Item)

    if ($null -eq $Item) {
        throw "A script result item is null."
    }

    $props = $Item.PSObject.Properties.Name
    foreach ($required in @("Script", "Status", "ExitCode", "Notes")) {
        if ($props -notcontains $required) {
            throw "Malformed result item detected; missing property '$required'."
        }
    }
}

function Get-ChangedPaths {
    $names = @()
    $raw = Invoke-GitSafe @("status", "--porcelain")
    if (-not $raw) {
        return @()
    }

    $lines = @($raw -split "`n" | Where-Object { $_.Trim() -ne "" })

    foreach ($line in $lines) {
        if ($line -match '^\S+\s+(.*)$') {
            $payload = $Matches[1]

            if ($payload -match '^(.*)\s+->\s+(.*)$') {
                $names += $Matches[1]
                $names += $Matches[2]
            }
            else {
                $names += $payload
            }
        }
    }

    return @($names | Where-Object { $_ -and $_.Trim() -ne "" } | Select-Object -Unique)
}

function Test-IsJournalPath {
    param([Parameter(Mandatory = $true)][string]$PathValue)

    $p = Normalize-RepoPath $PathValue
    return $p -like "data/journal/*"
}

function Test-IsAllowedWorkingTreePath {
    param(
        [Parameter(Mandatory = $true)][string]$PathValue,
        [string[]]$AllowedPaths
    )

    $candidate = Normalize-RepoPath $PathValue
    $allowed = @($AllowedPaths | ForEach-Object { Normalize-RepoPath $_ } | Select-Object -Unique)

    foreach ($item in $allowed) {
        if ($candidate -eq $item) {
            return $true
        }
    }

    return $false
}

function Get-BlockedPaths {
    param(
        [Parameter(Mandatory = $true)][string[]]$Paths,
        [string[]]$AllowedPaths
    )

    $blocked = @()

    foreach ($p in @($Paths)) {
        if (Test-IsJournalPath -PathValue $p) {
            continue
        }

        if (Test-IsAllowedWorkingTreePath -PathValue $p -AllowedPaths $AllowedPaths) {
            continue
        }

        $blocked += $p
    }

    return @($blocked | Select-Object -Unique)
}

function AllPathsAreJournal {
    param([string[]]$Paths)

    $pathsArray = @($Paths)
    if ($pathsArray.Count -eq 0) {
        return $false
    }

    foreach ($p in $pathsArray) {
        if (-not (Test-IsJournalPath -PathValue $p)) {
            return $false
        }
    }

    return $true
}

$originalLocation = Get-Location

try {
    Write-Host "== Final post-merge governance verification (journal-aware) ==" -ForegroundColor Green
    Set-Location -LiteralPath $RepoPath

    if (-not (Test-Path ".git")) {
        throw "Not a git repository: $RepoPath"
    }

    Write-Host "Step 1/7: Verify current branch and fetch remote" -ForegroundColor Yellow

    $currentBranch = Invoke-GitSafe @("rev-parse", "--abbrev-ref", "HEAD")
    if ($currentBranch -ne $BaseBranch) {
        throw "Current branch is '$currentBranch', expected '$BaseBranch'."
    }

    Invoke-GitSafe @("fetch", $RemoteName, "--prune") | Out-Null
    Write-Host "On $BaseBranch and remote fetched." -ForegroundColor Green

    Write-Host "Step 2/7: Check working tree (policy: $JournalPolicy) for journal-only or explicitly allowed changes" -ForegroundColor Yellow

    $changedPaths = @(Get-ChangedPaths)
    if ($changedPaths.Count -gt 0) {
        $blockedPaths = @(Get-BlockedPaths -Paths $changedPaths -AllowedPaths $AllowedWorkingTreePaths)
        $journal = @($changedPaths | Where-Object { Test-IsJournalPath -PathValue $_ } | Select-Object -Unique)

        if ($blockedPaths.Count -gt 0) {
            $text = ($blockedPaths | Sort-Object) -join "`n"
            throw "Working tree has blocked non-journal changes:`n$text"
        }

        $HasDirtyJournal = ($journal.Count -gt 0)

        if ($HasDirtyJournal) {
            switch ($JournalPolicy.ToLowerInvariant()) {
                "ignore" {
                    $JournalAction = "ignored"
                    Write-Host "Journal-only changes detected; continuing (ignored for governance)." -ForegroundColor DarkYellow
                }
                "stash" {
                    Write-Host "Stashing journal changes..." -ForegroundColor DarkYellow
                    Invoke-GitSafe @("stash", "push", "-m", "journal-auto-stash $(Get-Date -Format o)", "--", "data/journal/") | Out-Null
                    $JournalAction = "stashed"

                    $post = @(Get-ChangedPaths)
                    $postBlocked = @(Get-BlockedPaths -Paths $post -AllowedPaths $AllowedWorkingTreePaths)
                    if ($postBlocked.Count -gt 0) {
                        throw "Unexpected blocked changes after stash:`n$($postBlocked -join "`n")"
                    }

                    Write-Host "Journal changes stashed." -ForegroundColor Green
                }
                "commit" {
                    Write-Host "Committing journal changes (local only, no push)..." -ForegroundColor DarkYellow
                    Invoke-GitSafe @("add", "--", "data/journal/") | Out-Null

                    $stagedText = Invoke-GitSafe @("diff", "--cached", "--name-only")
                    $staged = @()
                    if ($stagedText) {
                        $staged = @($stagedText -split "`n" | Where-Object { $_.Trim() -ne "" })
                    }

                    if ($staged.Count -eq 0) {
                        $JournalAction = "ignored"
                        Write-Host "Nothing to commit after staging journal; continuing." -ForegroundColor DarkYellow
                    }
                    else {
                        $onlyJournalStaged = $true
                        foreach ($p in $staged) {
                            if (-not (Test-IsJournalPath -PathValue $p)) {
                                $onlyJournalStaged = $false
                                break
                            }
                        }

                        if (-not $onlyJournalStaged) {
                            throw "Staging included non-journal paths unexpectedly:`n$($staged -join "`n")"
                        }

                        Invoke-GitSafe @("commit", "-m", $JournalCommitMessage, "--no-verify") | Out-Null
                        $JournalAction = "committed"
                        $JournalCommitSha = Invoke-GitSafe @("rev-parse", "HEAD")
                        Write-Host "Committed journal changes at $JournalCommitSha" -ForegroundColor Green
                    }
                }
                default {
                    throw "Unknown JournalPolicy: $JournalPolicy. Use: ignore | stash | commit."
                }
            }
        }
        else {
            Write-Host "Working tree has only explicitly allowed changes." -ForegroundColor DarkYellow
        }
    }
    else {
        Write-Host "Working tree: clean" -ForegroundColor Green
    }

    Write-Host "Step 3/7: Verify alignment with $RemoteName/$BaseBranch (allow journal-only ahead)" -ForegroundColor Yellow

    $headSha = Invoke-GitSafe @("rev-parse", "HEAD")
    $remoteSha = Invoke-GitSafe @("rev-parse", "$RemoteName/$BaseBranch")

    if ($headSha -eq $remoteSha) {
        Write-Host "Aligned: $BaseBranch @ $headSha" -ForegroundColor Green
    }
    else {
        $diffNames = Invoke-GitSafe @("diff", "--name-only", "$RemoteName/$BaseBranch..HEAD")
        $diffArray = @()
        if ($diffNames) {
            $diffArray = @($diffNames -split "`n" | Where-Object { $_.Trim() -ne "" })
        }

        $onlyJournal = ($diffArray.Count -gt 0) -and (AllPathsAreJournal -Paths $diffArray)
        if ($onlyJournal) {
            $IsAllowedDivergence = $true
            $JournalAheadBy = [int](Invoke-GitSafe @("rev-list", "--count", "$RemoteName/$BaseBranch..HEAD"))
            Write-Host ("Allowed divergence: HEAD is ahead by {0} journal-only commit(s)." -f $JournalAheadBy) -ForegroundColor DarkYellow
        }
        else {
            $diffReport = if ($diffArray.Count -gt 0) { $diffArray -join "`n" } else { "(no paths listed)" }
            throw "$BaseBranch is not aligned with $RemoteName/$BaseBranch and differences include non-journal changes.`nHEAD=$headSha`nREMOTE=$remoteSha`nDIFF:`n$diffReport"
        }
    }

    Write-Host "Step 4/7: Verify merged artifact presence" -ForegroundColor Yellow

    if (-not (Test-Path $ArtifactPath)) {
        throw "Required artifact missing in working tree: $ArtifactPath"
    }

    $artifactTracked = Invoke-GitSafe @("ls-tree", "-r", "--name-only", "HEAD", "--", $ArtifactPath)
    if (-not $artifactTracked) {
        throw "Artifact is not present in HEAD tree: $ArtifactPath"
    }

    Write-Host "Artifact present and tracked: $ArtifactPath" -ForegroundColor Green

    Write-Host "Step 5/7: Verify finalization branch absence" -ForegroundColor Yellow

    $localBranch = Invoke-GitSafe @("branch", "--list", $FinalBranch)
    if ($localBranch) {
        throw "Local finalization branch still exists: $FinalBranch"
    }

    $remoteBranch = Invoke-GitSafe @("ls-remote", "--heads", $RemoteName, $FinalBranch)
    if ($remoteBranch) {
        throw "Remote finalization branch still exists: $RemoteName/$FinalBranch"
    }

    Write-Host "Finalization branch absent locally and remotely" -ForegroundColor Green

    Write-Host "Step 6/7: Run available governance scripts" -ForegroundColor Yellow

    $scriptsToRun = @($CandidateScripts | Where-Object { $_ -ne "scripts/verify-governance-closeout.ps1" } | Select-Object -Unique)
    $results = New-Object System.Collections.Generic.List[object]

    foreach ($script in $scriptsToRun) {
        $result = Invoke-OptionalPwshScript -ScriptPath $script
        Assert-ResultShape -Item $result
        [void]$results.Add($result)
    }

    Write-Host "Step 7/7: Summarize verification results" -ForegroundColor Yellow

    $failed = @($results | Where-Object { $_.Status -eq "FAILED" })
    $passed = @($results | Where-Object { $_.Status -eq "PASSED" })
    $skipped = @($results | Where-Object { $_.Status -like "SKIPPED*" })

    Write-Host ""
    Write-Host "== Verification summary ==" -ForegroundColor Green
    Write-Host "PASSED scripts : $($passed.Count)" -ForegroundColor Green
    Write-Host "SKIPPED scripts: $($skipped.Count)" -ForegroundColor DarkYellow
    Write-Host "FAILED scripts : $($failed.Count)" -ForegroundColor $(if ($failed.Count -eq 0) { "Green" } else { "Red" })

    if ($passed.Count -gt 0) {
        Write-Host ""
        Write-Host "Passed scripts:" -ForegroundColor Green
        foreach ($item in $passed) {
            Write-Host "  - $($item.Script)" -ForegroundColor Green
        }
    }

    if ($skipped.Count -gt 0) {
        Write-Host ""
        Write-Host "Skipped scripts:" -ForegroundColor DarkYellow
        foreach ($item in $skipped) {
            Write-Host "  - $($item.Script)" -ForegroundColor DarkYellow
        }
    }

    if ($failed.Count -gt 0) {
        Write-Host ""
        Write-Host "Failed scripts:" -ForegroundColor Red
        foreach ($item in $failed) {
            Write-Host "  - $($item.Script) | exit=$($item.ExitCode) | notes=$($item.Notes)" -ForegroundColor Red
        }
        throw "One or more available governance scripts failed."
    }

    $finalWT = @(Get-ChangedPaths)
    if ($finalWT.Count -gt 0) {
        $finalBlocked = @(Get-BlockedPaths -Paths $finalWT -AllowedPaths $AllowedWorkingTreePaths)
        if ($finalBlocked.Count -gt 0) {
            throw "Final working tree has blocked non-journal changes:`n$($finalBlocked -join "`n")"
        }
    }

    Write-Host ""
    Write-Host "== COMPLETE ==" -ForegroundColor Green

    if ($IsAllowedDivergence) {
        Write-Host "main is ahead of origin/main by $JournalAheadBy journal-only commit(s)." -ForegroundColor DarkYellow
    }
    else {
        Write-Host "main is aligned with origin/main." -ForegroundColor Green
    }

    if ($JournalAction -eq "stashed") {
        Write-Host "Journal: stashed (use 'git stash list' / 'git stash pop')." -ForegroundColor DarkYellow
    }
    elseif ($JournalAction -eq "committed") {
        Write-Host "Journal: committed locally at $JournalCommitSha (no push performed)." -ForegroundColor DarkYellow
    }
    elseif ($JournalAction -eq "ignored") {
        Write-Host "Journal: pending changes ignored for governance checks." -ForegroundColor DarkYellow
    }
    else {
        Write-Host "Journal: none or not applicable" -ForegroundColor Green
    }

    if (@($AllowedWorkingTreePaths).Count -gt 0) {
        Write-Host "Allowed working-tree paths:" -ForegroundColor DarkYellow
        foreach ($p in @($AllowedWorkingTreePaths)) {
            Write-Host "  - $p" -ForegroundColor DarkYellow
        }
    }

    Write-Host "Artifact verified: $ArtifactPath" -ForegroundColor Green
    Write-Host "Governance verification complete." -ForegroundColor Green
}
catch {
    Write-Host ""
    Write-Host "== FAILED ==" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "No reset, no push/force, and no shell exit was performed." -ForegroundColor Yellow
    Write-Host "Safe diagnostics:" -ForegroundColor Yellow
    Write-Host "  git status --short" -ForegroundColor Yellow
    Write-Host "  git branch --show-current" -ForegroundColor Yellow
    Write-Host "  git rev-parse HEAD" -ForegroundColor Yellow
    Write-Host "  git rev-parse origin/main" -ForegroundColor Yellow
    Write-Host "  git diff --name-only origin/main..HEAD" -ForegroundColor Yellow
}
finally {
    Set-Location $originalLocation
}