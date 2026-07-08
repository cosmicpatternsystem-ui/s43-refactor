param(
    [int]$IntervalSeconds = 120,
    [string]$ExpectedBranch = "phase17-work-from-restore"
)

$ErrorActionPreference = "Continue"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$LogFile = Join-Path $RepoRoot "AUTO_SNAPSHOT_LOG.md"
$SecurityBlockFile = Join-Path $RepoRoot "AUTO_SNAPSHOT_SECURITY_BLOCK.md"
$LockFile = Join-Path $RepoRoot ".auto_snapshot.lock"
$QualityGate = Join-Path $RepoRoot "tools\enterprise_quality_gate_phase17.ps1"

$RuntimeArtifacts = @(
    "AUTO_SNAPSHOT_LOG.md",
    "AUTO_SNAPSHOT_SECURITY_BLOCK.md",
    ".auto_snapshot.lock",
    "QUALITY_GATE_LAST_REPORT.md",
    "AUTO_SNAPSHOT_LAST_STATUS.json"
)

function Write-AutoLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

function Get-CurrentBranch {
    return (git branch --show-current).Trim()
}

function Test-OnlyIgnoredRuntimeChanges {
    $status = git status --porcelain --untracked-files=all
    if ([string]::IsNullOrWhiteSpace($status)) {
        return $true
    }

    foreach ($line in $status) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }

        $path = $line.Substring(3).Trim()
        if ($path -match " -> ") {
            $path = ($path -split " -> ")[-1].Trim()
        }

        $normalized = $path -replace "\\", "/"

        if ($RuntimeArtifacts -contains $path) { continue }
        if ($normalized -match "(^|/)__pycache__/") { continue }
        if ($normalized -match "\.pyc$|\.tmp$|\.temp$|\.bak$|\.swp$") { continue }

        return $false
    }

    return $true
}

function Unstage-RuntimeArtifacts {
    foreach ($artifact in $RuntimeArtifacts) {
        git reset -- $artifact *> $null
        git rm --cached --ignore-unmatch $artifact *> $null
    }

    git reset -- "__pycache__" "*.pyc" "*.tmp" "*.temp" "*.bak" "*.swp" *> $null
}

function Invoke-QualityGate {
    if (-not (Test-Path $QualityGate)) {
        Write-AutoLog "SECURITY BLOCK: quality gate script is missing."
        Add-Content -Path $SecurityBlockFile -Value "Quality gate script missing at $QualityGate" -Encoding UTF8
        return $false
    }

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File $QualityGate -ExpectedBranch $ExpectedBranch -Mode "AutoSnapshot"
    if ($LASTEXITCODE -ne 0) {
        Write-AutoLog "QUALITY BLOCK: enterprise quality gate failed. Commit/push stopped."
        Add-Content -Path $SecurityBlockFile -Value "Quality gate failed at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'). See QUALITY_GATE_LAST_REPORT.md locally." -Encoding UTF8
        return $false
    }

    return $true
}

function Invoke-AutoSnapshotOnce {
    git --version *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-AutoLog "ERROR: git is not available."
        return
    }

    $branch = Get-CurrentBranch
    if ($branch -ne $ExpectedBranch) {
        Write-AutoLog "Skipped: current branch is '$branch', expected '$ExpectedBranch'."
        return
    }

    git remote get-url origin *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-AutoLog "ERROR: origin remote is not configured."
        return
    }

    $status = git status --porcelain --untracked-files=all
    if ([string]::IsNullOrWhiteSpace($status)) {
        Write-AutoLog "No changes detected."
        return
    }

    if (Test-OnlyIgnoredRuntimeChanges) {
        Write-AutoLog "Only local runtime/noise changes detected. No commit needed."
        return
    }

    if (-not (Invoke-QualityGate)) {
        return
    }

    git add -A
    if ($LASTEXITCODE -ne 0) {
        Write-AutoLog "ERROR: git add failed."
        return
    }

    Unstage-RuntimeArtifacts

    $staged = git diff --cached --name-only
    if ([string]::IsNullOrWhiteSpace($staged)) {
        Write-AutoLog "No committable project changes after runtime exclusions."
        return
    }

    $commitId = Get-Date -Format "yyyyMMdd-HHmmss"
    $commitMessage = "Auto snapshot phase 17 validated work $commitId"

    git commit -m $commitMessage
    if ($LASTEXITCODE -ne 0) {
        Write-AutoLog "Commit skipped or failed."
        return
    }

    git push
    if ($LASTEXITCODE -eq 0) {
        Write-AutoLog "Committed and pushed validated snapshot: $commitMessage"
    }
    else {
        Write-AutoLog "ERROR: commit succeeded but push failed. Manual review needed."
    }
}

if (Test-Path $LockFile) {
    Write-AutoLog "Another auto snapshot process appears to be running. Exiting."
    exit 0
}

try {
    Set-Content -Path $LockFile -Value "$(Get-Date -Format o)" -Encoding ASCII
    Write-AutoLog "Hardened safe auto snapshot started. Branch=$ExpectedBranch IntervalSeconds=$IntervalSeconds"

    while ($true) {
        Invoke-AutoSnapshotOnce
        Start-Sleep -Seconds $IntervalSeconds
    }
}
finally {
    if (Test-Path $LockFile) {
        Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
    }
}
