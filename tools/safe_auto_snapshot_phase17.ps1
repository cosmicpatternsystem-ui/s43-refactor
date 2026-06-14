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

function Write-AutoLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

function Test-GitAvailable {
    git --version *> $null
    return ($LASTEXITCODE -eq 0)
}

function Get-CurrentBranch {
    return (git branch --show-current).Trim()
}

function Get-ChangedFilesForScan {
    $files = git diff --cached --name-only
    if ($LASTEXITCODE -ne 0) {
        return @()
    }

    $result = @()
    foreach ($file in $files) {
        if ([string]::IsNullOrWhiteSpace($file)) { continue }
        if ($file -like ".git/*") { continue }
        if ($file -like "AUTO_SNAPSHOT_LOG.md") { continue }

        $fullPath = Join-Path $RepoRoot $file
        if (-not (Test-Path $fullPath -PathType Leaf)) { continue }

        try {
            $item = Get-Item $fullPath
            if ($item.Length -gt 5242880) {
                Write-AutoLog "Secret scan skipped large file over 5MB: $file"
                continue
            }
            $result += $file
        }
        catch {
            Write-AutoLog "Could not inspect file for secret scan: $file"
        }
    }

    return $result
}

function Test-SecretRisk {
    param([string[]]$Files)

    $findings = @()

    $regexRules = @(
        @{ Name = "AWS access key"; Pattern = "AKIA[0-9A-Z]{16}" },
        @{ Name = "AWS temp access key"; Pattern = "ASIA[0-9A-Z]{16}" },
        @{ Name = "GitHub token"; Pattern = "gh[pousr]_[A-Za-z0-9_]{36,255}" },
        @{ Name = "Slack token"; Pattern = "xox[baprs]-[A-Za-z0-9-]{10,}" },
        @{ Name = "Private key block"; Pattern = "-----BEGIN (RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----" },
        @{ Name = "Generic password assignment"; Pattern = "(?i)(password|passwd|pwd)\s*[:=]\s*['""][^'""]{8,}['""]" },
        @{ Name = "Generic token assignment"; Pattern = "(?i)(token|secret|api_key|apikey)\s*[:=]\s*['""][^'""]{12,}['""]" }
    )

    foreach ($file in $Files) {
        $fullPath = Join-Path $RepoRoot $file
        try {
            $content = Get-Content -Raw -Path $fullPath -Encoding UTF8 -ErrorAction Stop
        }
        catch {
            try {
                $content = Get-Content -Raw -Path $fullPath -ErrorAction Stop
            }
            catch {
                Write-AutoLog "Secret scan could not read file: $file"
                continue
            }
        }

        foreach ($rule in $regexRules) {
            if ($content -match $rule.Pattern) {
                $findings += "- $($rule.Name): $file"
            }
        }
    }

    if ($findings.Count -gt 0) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $report = @()
        $report += ""
        $report += "## Auto Snapshot Security Block - $timestamp"
        $report += ""
        $report += "Auto commit/push was blocked because possible secrets were detected."
        $report += ""
        $report += $findings
        $report += ""
        $report += "Review these files manually. If this is a false positive, commit manually after verification."
        Add-Content -Path $SecurityBlockFile -Value ($report -join [Environment]::NewLine) -Encoding UTF8
        return $true
    }

    return $false
}

function Invoke-AutoSnapshotOnce {
    if (-not (Test-GitAvailable)) {
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

    $status = git status --porcelain
    if ([string]::IsNullOrWhiteSpace($status)) {
        Write-AutoLog "No changes detected."
        return
    }

    git add -A
    if ($LASTEXITCODE -ne 0) {
        Write-AutoLog "ERROR: git add failed."
        return
    }

    $scanFiles = Get-ChangedFilesForScan
    if (Test-SecretRisk -Files $scanFiles) {
        git reset *> $null
        Write-AutoLog "SECURITY BLOCK: possible secret detected. Commit/push stopped."
        return
    }

    $commitId = Get-Date -Format "yyyyMMdd-HHmmss"
    $commitMessage = "Auto snapshot phase 17 work $commitId"

    git commit -m $commitMessage
    if ($LASTEXITCODE -ne 0) {
        Write-AutoLog "Commit skipped or failed."
        return
    }

    git push
    if ($LASTEXITCODE -eq 0) {
        Write-AutoLog "Committed and pushed: $commitMessage"
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
    Write-AutoLog "Safe auto snapshot started. Branch=$ExpectedBranch IntervalSeconds=$IntervalSeconds"

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
