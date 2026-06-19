[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Message,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string[]]$Paths
)

$ErrorActionPreference = "Stop"

$Branch = "phase17-work-from-restore"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ApprovedSync = Join-Path $PSScriptRoot "phase17_approved_sync.ps1"

Set-Location -LiteralPath $RepoRoot

if (-not (Test-Path -LiteralPath $ApprovedSync)) {
    throw "Approved sync script not found: $ApprovedSync"
}

$CurrentBranch = (git branch --show-current).Trim()
if ($CurrentBranch -ne $Branch) {
    throw "Invalid branch: $CurrentBranch"
}

$BeforeStatus = @(git status --short)
if ($BeforeStatus.Count -gt 0) {
    Write-Host "Pre-sync working tree contains intended changes:"
    $BeforeStatus | ForEach-Object { Write-Host $_ }
}

$Params = @{
    Message = $Message
    Paths = $Paths
    Push = $true
}

& $ApprovedSync @Params

git fetch origin $Branch | Out-Null

$Head = (git rev-parse HEAD).Trim()
$Origin = (git rev-parse "origin/$Branch").Trim()
$AfterStatus = @(git status --short)

if ($Head -ne $Origin) {
    throw "HEAD and origin differ after approved sync push. HEAD=$Head ORIGIN=$Origin"
}

if ($AfterStatus.Count -gt 0) {
    throw ("Working tree is not clean after approved sync push: " + ($AfterStatus -join " | "))
}

Write-Host "PHASE18_APPROVED_SYNC_WRAPPER_PASS"
Write-Host "HEAD=$Head"
Write-Host "ORIGIN=$Origin"
