param(
    [Parameter(Mandatory = $true)]
    [string]$Message,

    [Parameter(Mandatory = $true)]
    [string[]]$Paths,

    [string]$ExpectedBranch = "phase17-work-from-restore",

    [ValidateSet("PreRestart", "PostStart")]
    [string]$HealthMode = "PreRestart",

    [string]$Remote = "origin",

    [switch]$Push
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Fail([string]$Message) {
    Write-Error $Message
    exit 1
}

function Invoke-Git([string[]]$Arguments) {
    & git @Arguments
    if ($LASTEXITCODE -ne 0) {
        Fail "git command failed: git $($Arguments -join ' ')"
    }
}

function Get-GitOutput([string[]]$Arguments) {
    $output = & git @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        Fail "git command failed: git $($Arguments -join ' ')`n$output"
    }
    return @($output)
}

function Convert-ToRepoRelative([string]$InputPath, [string]$RepoRoot) {
    $resolved = Resolve-Path -LiteralPath $InputPath -ErrorAction Stop
    $fullPath = $resolved.Path
    $rootPath = (Resolve-Path -LiteralPath $RepoRoot).Path.TrimEnd("\", "/")

    if (-not $fullPath.StartsWith($rootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        Fail "Path is outside repository: $InputPath"
    }

    return $fullPath.Substring($rootPath.Length).TrimStart("\", "/").Replace("\", "/")
}

function Get-StatusPath([string]$StatusLine) {
    if ($StatusLine.Length -lt 4) {
        return $null
    }

    $path = $StatusLine.Substring(3).Trim()

    if ($path.Contains(" -> ")) {
        $path = ($path -split " -> ")[-1].Trim()
    }

    return $path.Trim('"').Replace("\", "/")
}

$repoRoot = @(Get-GitOutput @("rev-parse", "--show-toplevel"))[0]
Set-Location -LiteralPath $repoRoot

$currentBranch = @(Get-GitOutput @("branch", "--show-current"))[0]
if ($currentBranch -ne $ExpectedBranch) {
    Fail "Branch mismatch. Current: $currentBranch Expected: $ExpectedBranch"
}

if ([string]::IsNullOrWhiteSpace($Message)) {
    Fail "Commit message must not be empty."
}

$approvedPaths = @()
foreach ($path in $Paths) {
    $approvedPaths += Convert-ToRepoRelative -InputPath $path -RepoRoot $repoRoot
}

$status = @(Get-GitOutput @("status", "--porcelain", "--untracked-files=all"))
if ($status.Count -eq 0) {
    Fail "No changes to sync."
}

$approvedLookup = @{}
foreach ($path in $approvedPaths) {
    $approvedLookup[$path.ToLowerInvariant()] = $true
}

$unexpected = @()
foreach ($line in $status) {
    $statusPath = Get-StatusPath -StatusLine $line
    if ($null -eq $statusPath) {
        continue
    }

    if (-not $approvedLookup.ContainsKey($statusPath.ToLowerInvariant())) {
        $unexpected += "$line"
    }
}

if ($unexpected.Count -gt 0) {
    Write-Host "Unexpected working tree changes detected:"
    $unexpected | ForEach-Object { Write-Host $_ }
    Fail "Refusing to sync because unapproved paths are dirty."
}

$qualityScript = Join-Path $repoRoot "tools\enterprise_quality_gate_phase17.ps1"
if (-not (Test-Path -LiteralPath $qualityScript)) {
    Fail "Quality gate script not found: $qualityScript"
}

Write-Host "=== Phase 17 Approved Sync ==="
Write-Host "Repo: $repoRoot"
Write-Host "Branch: $currentBranch"
Write-Host "Approved paths:"
$approvedPaths | ForEach-Object { Write-Host " - $_" }

Write-Host "=== Running quality gate ==="
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $qualityScript
if ($LASTEXITCODE -ne 0) {
    Fail "Quality gate failed. Nothing was committed or pushed."
}

$addArgs = @("add", "--") + $approvedPaths
Invoke-Git $addArgs

Write-Host "=== Checking staged whitespace ==="
& git diff --cached --check -- @approvedPaths
if ($LASTEXITCODE -ne 0) {
    Fail "Staged diff check failed. Fix whitespace before commit."
}

& git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Fail "No staged changes after approved add."
}

Write-Host "=== Creating commit ==="
Invoke-Git @("commit", "-m", $Message)

$healthScript = Join-Path $repoRoot "tools\phase17_worker_health_check.ps1"
if (-not (Test-Path -LiteralPath $healthScript)) {
    Fail "Health check script not found: $healthScript"
}

Write-Host "=== Running health check ==="
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $healthScript -Mode $HealthMode
if ($LASTEXITCODE -ne 0) {
    Fail "Health check failed after commit. Push was not attempted."
}

if ($Push.IsPresent) {
    Write-Host "=== Pushing to remote ==="
    Invoke-Git @("push", $Remote, $currentBranch)
}
else {
    Write-Host "Push skipped because -Push was not provided."
}

Write-Host "=== Final status ==="
Invoke-Git @("status", "--short")

$head = @(Get-GitOutput @("log", "--oneline", "-1"))[0]
Write-Host "APPROVED_SYNC_PASS"
Write-Host "HEAD: $head"
