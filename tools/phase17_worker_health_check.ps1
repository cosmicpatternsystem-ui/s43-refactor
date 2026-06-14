param(
    [string]$ExpectedBranch = "phase17-work-from-restore",
    [ValidateSet("PostStart", "PreRestart")]
    [string]$Mode = "PostStart"
)

$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$branch = (git rev-parse --abbrev-ref HEAD).Trim()
$head = (git log --oneline -1).Trim()
$status = git status --short

$workers = @(Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like "*safe_auto_snapshot_phase17.ps1*" })

Write-Host "=== Phase 17 Worker Health Check ==="
Write-Host "Repo: $repoRoot"
Write-Host "Branch: $branch"
Write-Host "Expected branch: $ExpectedBranch"
Write-Host "HEAD: $head"
Write-Host "Mode: $Mode"
Write-Host "Worker count: $($workers.Count)"

if ($workers.Count -gt 0) {
    $workers | Select-Object ProcessId, CommandLine | Format-Table -AutoSize
}

if ($branch -ne $ExpectedBranch) {
    Write-Host "HEALTH_FAIL: wrong branch"
    exit 1
}

if ($status) {
    Write-Host "HEALTH_FAIL: working tree is not clean"
    $status | Out-Host
    exit 1
}

if ($Mode -eq "PostStart" -and $workers.Count -ne 1) {
    Write-Host "HEALTH_FAIL: expected exactly one worker in PostStart mode"
    exit 1
}

if ($Mode -eq "PreRestart" -and $workers.Count -ne 0) {
    Write-Host "HEALTH_FAIL: expected zero workers before restart"
    exit 1
}

$qualityGatePath = Join-Path $repoRoot "tools/enterprise_quality_gate_phase17.ps1"
if (-not (Test-Path $qualityGatePath)) {
    Write-Host "HEALTH_FAIL: quality gate script not found"
    exit 1
}

powershell -NoProfile -ExecutionPolicy Bypass -File $qualityGatePath -ExpectedBranch $ExpectedBranch -Mode PreCommit
if ($LASTEXITCODE -ne 0) {
    Write-Host "HEALTH_FAIL: quality gate failed"
    exit 1
}

Write-Host "HEALTH_PASS"
exit 0
