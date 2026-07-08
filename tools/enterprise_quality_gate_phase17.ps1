param(
    [string]$ExpectedBranch = "phase17-work-from-restore",
    [string]$Mode = "ManualVerification"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptDir '..'))

if (-not (Test-Path -LiteralPath (Join-Path $repoRoot '.git'))) {
    throw "Unable to resolve repository root from script location: $repoRoot"
}

Set-Location -LiteralPath $repoRoot

$failures = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]
$started = Get-Date

function Add-Failure {
    param([string]$Message)
    $script:failures.Add($Message) | Out-Null
}

function Add-Warning {
    param([string]$Message)
    $script:warnings.Add($Message) | Out-Null
}

function Test-GitCommandSuccess {
    param(
        [string]$Description,
        [scriptblock]$Command
    )

    try {
        & $Command
        if ($LASTEXITCODE -ne 0) {
            Add-Failure "$Description failed."
        }
    }
    catch {
        Add-Failure "$Description failed: $($_.Exception.Message)"
    }
}

$currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
if ($currentBranch -ne $ExpectedBranch) {
    Add-Failure "Wrong branch: $currentBranch. Expected: $ExpectedBranch"
}

if (Test-Path ".git\MERGE_HEAD") {
    Add-Failure "Repository is in merge state."
}

if ((Test-Path ".git\rebase-merge") -or (Test-Path ".git\rebase-apply")) {
    Add-Failure "Repository is in rebase state."
}

if (Test-Path ".git\CHERRY_PICK_HEAD") {
    Add-Failure "Repository is in cherry-pick state."
}

Test-GitCommandSuccess "git diff --check" { git diff --check | Out-Host }
Test-GitCommandSuccess "git diff --cached --check" { git diff --cached --check | Out-Host }

# Conflict marker scan across tracked text files.
try {
    $conflictMatches = git grep -n -E "^(<<<<<<<( .*)?|=======$|>>>>>>>( .*)?)$" -- . 2>$null
    if ($LASTEXITCODE -eq 0 -and $conflictMatches) {
        Add-Failure "Conflict markers found:`n$conflictMatches"
    }
}
catch {
    Add-Failure "Conflict marker scan failed: $($_.Exception.Message)"
}

# Secret scan. This is intentionally conservative; real secret scanning should also run in CI.
$secretPatterns = @(
    "AKIA[0-9A-Z]{16}",
    "ASIA[0-9A-Z]{16}",
    "ghp_[A-Za-z0-9_]{30,}",
    "github_pat_[A-Za-z0-9_]{20,}",
    "xox[baprs]-[A-Za-z0-9-]{20,}",
    "-----BEGIN (RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----",
    "(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['""][^'""]{12,}['""]"
)

$excludedSecretScanPaths = @(
    "AUTO_SNAPSHOT_LOG.md",
    "QUALITY_GATE_LAST_REPORT.md"
)

try {
    $trackedFiles = git ls-files
    foreach ($file in $trackedFiles) {
        if ([string]::IsNullOrWhiteSpace($file)) { continue }
        if ($excludedSecretScanPaths -contains $file) { continue }
        if (-not (Test-Path $file)) { continue }

        $size = (Get-Item $file).Length
        if ($size -gt 1048576) {
            Add-Warning "Secret scan skipped large file over 1MB: $file"
            continue
        }

        $content = Get-Content $file -Raw -ErrorAction SilentlyContinue
        if ($null -eq $content) { continue }

        foreach ($pattern in $secretPatterns) {
            if ($content -match $pattern) {
                Add-Failure "Possible secret detected in tracked file: $file"
                break
            }
        }
    }
}
catch {
    Add-Failure "Secret scan failed: $($_.Exception.Message)"
}

# Python syntax check for known Python entry files.
$pythonCandidates = @("s43.py", "main.py", "app.py")
foreach ($pyFile in $pythonCandidates) {
    if (Test-Path $pyFile) {
        $pythonChecked = $false

        try {
            py -3 -m py_compile $pyFile
            if ($LASTEXITCODE -eq 0) {
                $pythonChecked = $true
            }
        }
        catch {}

        if (-not $pythonChecked) {
            try {
                python -m py_compile $pyFile
                if ($LASTEXITCODE -eq 0) {
                    $pythonChecked = $true
                }
            }
            catch {}
        }

        if (-not $pythonChecked) {
            Add-Failure "Python syntax check failed or Python is unavailable for: $pyFile"
        }
    }
}

# Optional pytest if tests exist.
if ((Test-Path "tests") -or (Test-Path "pytest.ini") -or (Test-Path "pyproject.toml")) {
    try {
        python -m pytest -q
        if ($LASTEXITCODE -ne 0) {
            Add-Failure "pytest failed."
        }
    }
    catch {
        Add-Warning "pytest could not be executed: $($_.Exception.Message)"
    }
}

$finished = Get-Date
$result = if ($failures.Count -eq 0) { "PASS" } else { "FAIL" }

$report = New-Object System.Collections.Generic.List[string]
$report.Add("# Phase 17 Quality Gate Last Report") | Out-Null
$report.Add("") | Out-Null
$report.Add("- Started: $($started.ToString('yyyy-MM-dd HH:mm:ss'))") | Out-Null
$report.Add("- Finished: $($finished.ToString('yyyy-MM-dd HH:mm:ss'))") | Out-Null
$report.Add("- Mode: $Mode") | Out-Null
$report.Add("- Expected branch: $ExpectedBranch") | Out-Null
$report.Add("- Actual branch: $currentBranch") | Out-Null
$report.Add("- Result: $result") | Out-Null
$report.Add("") | Out-Null
$report.Add("## Failures") | Out-Null

if ($failures.Count -eq 0) {
    $report.Add("- None") | Out-Null
}
else {
    foreach ($failure in $failures) {
        $report.Add("- $failure") | Out-Null
    }
}

$report.Add("") | Out-Null
$report.Add("## Warnings") | Out-Null

if ($warnings.Count -eq 0) {
    $report.Add("- None") | Out-Null
}
else {
    foreach ($warning in $warnings) {
        $report.Add("- $warning") | Out-Null
    }
}

Set-Content -Path "QUALITY_GATE_LAST_REPORT.md" -Value $report -Encoding UTF8

if ($result -eq "PASS") {
    Write-Host "QUALITY_GATE_PASS"
    exit 0
}

Write-Host "QUALITY_GATE_FAIL"
exit 1
