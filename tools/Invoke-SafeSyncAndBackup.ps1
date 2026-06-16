[CmdletBinding()]
param(
    [string]$CommitMessage = "",
    [string]$BackupRoot = "E:\saead\ssl\s43_project_backups",
    [switch]$SkipTests,
    [switch]$AllowUntrackedBackup
)

$ErrorActionPreference = "Stop"

function Run {
    param([string]$Command)
    Write-Host ""
    Write-Host ">>> $Command"
    cmd /c $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $Command"
    }
}

function GitOutput {
    param([string]$ArgsLine)
    $out = git $ArgsLine.Split(" ")
    if ($LASTEXITCODE -ne 0) {
        throw "git $ArgsLine failed"
    }
    return $out
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$branch = (git branch --show-current).Trim()
if ([string]::IsNullOrWhiteSpace($branch)) {
    throw "Detached HEAD is not allowed."
}

Write-Host "Repo: $repoRoot"
Write-Host "Branch: $branch"

Run "git fetch --prune origin"

$upstream = ""
try {
    $upstream = (git rev-parse --abbrev-ref --symbolic-full-name "@{u}").Trim()
} catch {
    throw "No upstream configured for branch $branch."
}

$localHead = (git rev-parse HEAD).Trim()
$remoteHead = (git rev-parse "@{u}").Trim()
$baseHead = (git merge-base HEAD "@{u}").Trim()

if ($localHead -ne $remoteHead) {
    if ($localHead -eq $baseHead) {
        throw "Local branch is behind $upstream. Pull/rebase manually before continuing."
    }
    if ($remoteHead -eq $baseHead) {
        Write-Host "Local branch is ahead of $upstream."
    } else {
        throw "Local and remote branches have diverged. Manual review required."
    }
}

$shortStatus = git status --short
$untracked = $shortStatus | Where-Object { $_ -like "?? *" }

if ($untracked.Count -gt 0 -and -not $AllowUntrackedBackup) {
    Write-Host ""
    Write-Host "Untracked files detected:"
    $untracked | ForEach-Object { Write-Host $_ }
    throw "Untracked files require an explicit decision. Re-run with -AllowUntrackedBackup to include them in physical backup only, or git add them intentionally."
}

if (-not $SkipTests) {
    Run "pytest -q"
}

Run "git diff --check"

$porcelainBeforeCommit = git status --porcelain
if ($porcelainBeforeCommit.Count -gt 0) {
    if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
        git status --short
        throw "Workspace has changes. Provide -CommitMessage to commit intentionally."
    }

    Run "git add -A"
    Run "git diff --cached --check"
    Run "git commit -m ""$CommitMessage"""
} else {
    Write-Host "No working tree changes to commit."
}

$localHeadAfterCommit = (git rev-parse HEAD).Trim()
$remoteHeadAfterFetch = (git rev-parse "@{u}").Trim()
$baseAfterCommit = (git merge-base HEAD "@{u}").Trim()

if ($localHeadAfterCommit -ne $remoteHeadAfterFetch) {
    if ($remoteHeadAfterFetch -eq $baseAfterCommit) {
        Run "git push"
    } else {
        throw "Remote changed during operation. Manual review required."
    }
} else {
    Write-Host "No push needed."
}

Run "git fetch --prune origin"

$finalLocal = (git rev-parse HEAD).Trim()
$finalRemote = (git rev-parse "@{u}").Trim()

if ($finalLocal -ne $finalRemote) {
    throw "Final verification failed: local HEAD differs from upstream."
}

$finalStatus = git status --porcelain
if ($finalStatus.Count -gt 0) {
    git status --short
    throw "Final verification failed: workspace is not clean."
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $BackupRoot "$branch`_$timestamp`_$($finalLocal.Substring(0, 12))"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

$archivePath = Join-Path $backupDir "tracked_source.zip"
Run "git archive --format=zip --output=""$archivePath"" HEAD"

$metaPath = Join-Path $backupDir "verification.txt"
@(
    "repo=$repoRoot"
    "branch=$branch"
    "upstream=$upstream"
    "head=$finalLocal"
    "created_utc=$((Get-Date).ToUniversalTime().ToString("o"))"
    ""
    "git_status:"
    "$(git status)"
    ""
    "git_log:"
    "$(git log --oneline -5)"
) | Set-Content -Path $metaPath -Encoding UTF8

if ($AllowUntrackedBackup -and $untracked.Count -gt 0) {
    $untrackedDir = Join-Path $backupDir "untracked_files"
    New-Item -ItemType Directory -Force -Path $untrackedDir | Out-Null

    foreach ($line in $untracked) {
        $relative = $line.Substring(3)
        $source = Join-Path $repoRoot $relative
        if (Test-Path $source) {
            $target = Join-Path $untrackedDir $relative
            $targetParent = Split-Path -Parent $target
            New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
            Copy-Item -Path $source -Destination $target -Recurse -Force
        }
    }
}

Write-Host ""
Write-Host "SAFE SYNC COMPLETE"
Write-Host "Branch: $branch"
Write-Host "HEAD: $finalLocal"
Write-Host "Upstream: $upstream"
Write-Host "Backup: $backupDir"
Write-Host "Workspace: clean"
Write-Host "Remote: synced"
