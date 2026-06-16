[CmdletBinding()]
param(
    [string]$CommitMessage = "",
    [string]$BackupRoot = "E:\saead\ssl\s43_project_backups",
    [switch]$SkipTests,
    [switch]$AllowUntrackedBackup
)

$ErrorActionPreference = "Stop"

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$Exe,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$NativeArgs
    )

    Write-Host ""
    Write-Host ">>> $Exe $($NativeArgs -join ' ')"
    & $Exe @NativeArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $Exe $($NativeArgs -join ' ')"
    }
}

function Get-GitText {
    param([Parameter(Mandatory = $true)][string[]]$Args)

    $out = & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git $($NativeArgs -join ' ') failed"
    }
    return $out
}

function New-TrackedManifest {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$OutputPath
    )

    $lines = New-Object System.Collections.Generic.List[string]
    $tracked = Get-GitText @("ls-files")

    foreach ($relative in $tracked) {
        $localRelative = $relative -replace "/", [System.IO.Path]::DirectorySeparatorChar
        $fullPath = Join-Path $RepoRoot $localRelative

        if (Test-Path -LiteralPath $fullPath -PathType Leaf) {
            $hash = Get-FileHash -LiteralPath $fullPath -Algorithm SHA256
            $normalized = $relative -replace "\\", "/"
            $lines.Add("$($hash.Hash.ToLowerInvariant()) *$normalized")
        }
    }

    $lines | Sort-Object | Set-Content -LiteralPath $OutputPath -Encoding UTF8
}

function New-ArtifactHashes {
    param(
        [Parameter(Mandatory = $true)][string]$BackupDir,
        [Parameter(Mandatory = $true)][string]$OutputPath
    )

    $artifactLines = New-Object System.Collections.Generic.List[string]
    $files = Get-ChildItem -LiteralPath $BackupDir -File | Where-Object {
        $_.Name -ne (Split-Path -Leaf $OutputPath) -and $_.Name -ne "verification.txt"
    }

    foreach ($file in $files) {
        $hash = Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256
        $artifactLines.Add("$($hash.Hash.ToLowerInvariant()) *$($file.Name)")
    }

    $artifactLines | Sort-Object | Set-Content -LiteralPath $OutputPath -Encoding UTF8
}

function Test-ArtifactHashes {
    param(
        [Parameter(Mandatory = $true)][string]$BackupDir,
        [Parameter(Mandatory = $true)][string]$HashFile
    )

    $lines = Get-Content -LiteralPath $HashFile
    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        $parts = $line -split " \*", 2
        if ($parts.Count -ne 2) {
            throw "Invalid artifact hash line: $line"
        }

        $expected = $parts[0].Trim().ToLowerInvariant()
        $name = $parts[1].Trim()
        $path = Join-Path $BackupDir $name

        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Missing artifact during verification: $name"
        }

        $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $expected) {
            throw "Artifact hash mismatch: $name"
        }
    }
}

$repoRoot = (Get-GitText @("rev-parse", "--show-toplevel")).Trim()
Set-Location $repoRoot

$branch = (Get-GitText @("branch", "--show-current")).Trim()
if ([string]::IsNullOrWhiteSpace($branch)) {
    throw "Detached HEAD is not allowed."
}

Write-Host "Repo: $repoRoot"
Write-Host "Branch: $branch"

Invoke-Native git fetch --prune origin

try {
    $upstream = (Get-GitText @("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")).Trim()
} catch {
    throw "No upstream configured for branch $branch."
}

$localHead = (Get-GitText @("rev-parse", "HEAD")).Trim()
$remoteHead = (Get-GitText @("rev-parse", "@{u}")).Trim()
$baseHead = (Get-GitText @("merge-base", "HEAD", "@{u}")).Trim()

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

$shortStatus = Get-GitText @("status", "--short")
$untracked = @($shortStatus | Where-Object { $_ -match "^\?\? " })

if ($untracked.Count -gt 0 -and -not $AllowUntrackedBackup) {
    Write-Host ""
    Write-Host "Untracked files detected:"
    $untracked | ForEach-Object { Write-Host $_ }
    throw "Untracked files require an explicit decision. Re-run with -AllowUntrackedBackup to include them in physical backup only, or git add them intentionally."
}

if (-not $SkipTests) {
    Invoke-Native pytest -q
}

Invoke-Native git diff --check

$porcelainBeforeCommit = @(Get-GitText @("status", "--porcelain"))
if ($porcelainBeforeCommit.Count -gt 0) {
    if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
        Invoke-Native git status --short
        throw "Workspace has changes. Provide -CommitMessage to commit intentionally."
    }

    Invoke-Native git add -A
    Invoke-Native git diff --cached --check
    Invoke-Native git commit -m $CommitMessage
} else {
    Write-Host "No working tree changes to commit."
}

$localHeadAfterCommit = (Get-GitText @("rev-parse", "HEAD")).Trim()
$remoteHeadAfterFetch = (Get-GitText @("rev-parse", "@{u}")).Trim()
$baseAfterCommit = (Get-GitText @("merge-base", "HEAD", "@{u}")).Trim()

if ($localHeadAfterCommit -ne $remoteHeadAfterFetch) {
    if ($remoteHeadAfterFetch -eq $baseAfterCommit) {
        Invoke-Native git push
    } else {
        throw "Remote changed during operation. Manual review required."
    }
} else {
    Write-Host "No push needed."
}

Invoke-Native git fetch --prune origin

$finalLocal = (Get-GitText @("rev-parse", "HEAD")).Trim()
$finalRemote = (Get-GitText @("rev-parse", "@{u}")).Trim()

if ($finalLocal -ne $finalRemote) {
    throw "Final verification failed: local HEAD differs from upstream."
}

$finalStatus = @(Get-GitText @("status", "--porcelain"))
if ($finalStatus.Count -gt 0) {
    Invoke-Native git status --short
    throw "Final verification failed: workspace is not clean."
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $BackupRoot "$branch`_$timestamp`_$($finalLocal.Substring(0, 12))"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

$archivePath = Join-Path $backupDir "tracked_source.zip"
$bundlePath = Join-Path $backupDir "repo.bundle"
$manifestPath = Join-Path $backupDir "manifest.sha256"
$artifactsPath = Join-Path $backupDir "artifacts.sha256"
$statusJsonPath = Join-Path $backupDir "status.json"
$verificationPath = Join-Path $backupDir "verification.txt"
$restorePath = Join-Path $backupDir "RESTORE_INSTRUCTIONS.txt"

Invoke-Native git archive --format=zip "--output=$archivePath" HEAD
Invoke-Native git bundle create $bundlePath --all

New-TrackedManifest -RepoRoot $repoRoot -OutputPath $manifestPath

$statusObject = [ordered]@{
    repo = $repoRoot
    branch = $branch
    upstream = $upstream
    head = $finalLocal
    remote_head = $finalRemote
    remote_url = @(Get-GitText @("remote", "get-url", "origin"))[0]
    backup_dir = $backupDir
    created_utc = (Get-Date).ToUniversalTime().ToString("o")
    tests = $(if ($SkipTests) { "skipped" } else { "passed" })
    workspace = "clean"
    remote = "synced"
    untracked_included = [bool]$AllowUntrackedBackup
}

$statusObject | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $statusJsonPath -Encoding UTF8

@(
    "repo=$repoRoot"
    "branch=$branch"
    "upstream=$upstream"
    "head=$finalLocal"
    "remote_head=$finalRemote"
    "created_utc=$((Get-Date).ToUniversalTime().ToString("o"))"
    "backup_dir=$backupDir"
    "tracked_source=$archivePath"
    "repo_bundle=$bundlePath"
    "tracked_manifest=$manifestPath"
    "artifact_hashes=$artifactsPath"
    ""
    "git_status:"
    "$(git status)"
    ""
    "git_log:"
    "$(git log --oneline -5)"
) | Set-Content -LiteralPath $verificationPath -Encoding UTF8

@(
    "S43 Disaster Recovery Instructions"
    ""
    "1. Restore from GitHub:"
    "   git clone $($statusObject.remote_url)"
    "   cd s43-refactor"
    "   git checkout $branch"
    ""
    "2. Restore from repo.bundle if GitHub is unavailable:"
    "   git clone repo.bundle s43-refactor-restored"
    "   cd s43-refactor-restored"
    "   git checkout $branch"
    ""
    "3. Restore source snapshot only:"
    "   Expand tracked_source.zip into a clean directory."
    ""
    "4. Verify backup artifact integrity:"
    "   Compare SHA256 values in artifacts.sha256 with Get-FileHash outputs."
    ""
    "5. Verify tracked file integrity after restore:"
    "   Compare manifest.sha256 against restored tracked files."
    ""
    "Recorded head:"
    "   $finalLocal"
) | Set-Content -LiteralPath $restorePath -Encoding UTF8

if ($AllowUntrackedBackup -and $untracked.Count -gt 0) {
    $untrackedDir = Join-Path $backupDir "untracked_files"
    New-Item -ItemType Directory -Force -Path $untrackedDir | Out-Null

    foreach ($line in $untracked) {
        $relative = $line.Substring(3)
        $source = Join-Path $repoRoot $relative
        if (Test-Path -LiteralPath $source) {
            $target = Join-Path $untrackedDir $relative
            $targetParent = Split-Path -Parent $target
            New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
            Copy-Item -LiteralPath $source -Destination $target -Recurse -Force
        }
    }
}

New-ArtifactHashes -BackupDir $backupDir -OutputPath $artifactsPath
Test-ArtifactHashes -BackupDir $backupDir -HashFile $artifactsPath

Write-Host ""
Write-Host "SAFE SYNC AND DISASTER RECOVERY BACKUP COMPLETE"
Write-Host "Branch: $branch"
Write-Host "HEAD: $finalLocal"
Write-Host "Upstream: $upstream"
Write-Host "Backup: $backupDir"
Write-Host "Source archive: $archivePath"
Write-Host "Git bundle: $bundlePath"
Write-Host "Manifest: $manifestPath"
Write-Host "Status JSON: $statusJsonPath"
Write-Host "Workspace: clean"
Write-Host "Remote: synced"
