[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [string]$ExpectedBranch = 'chore/readiness-no-go-state',
    [string]$Remote = 'origin',
    [string]$BaseBranch = 'main',
    [string]$ExpectedCommit = '02e905d',
    [string]$CommitMessage = 'record commercial readiness no-go state',
    [string]$PrTitle = 'Record commercial readiness NO-GO state',
    [switch]$OpenPr
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-Git {
    param([Parameter(Mandatory)][string[]]$Arguments, [switch]$AllowFailure)
    & git @Arguments
    if ($LASTEXITCODE -ne 0 -and -not $AllowFailure) { throw "git failed." }
}

function Get-GitOutput {
    param([Parameter(Mandatory)][string[]]$Arguments)
    $output = & git @Arguments
    if ($LASTEXITCODE -ne 0) { throw "git failed." }
    return ($output | Out-String).Trim()
}

function Invoke-GovernanceValidateIsolated {
    param([Parameter(Mandatory)][string]$WorkingDirectory, [Parameter(Mandatory)][string]$ScriptPath)
    $validateCmd = "Set-Location -LiteralPath '$WorkingDirectory'; & '$ScriptPath' validate; exit `$LASTEXITCODE"
    $output = & powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command $validateCmd 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Governance validation failed." }
    Write-Host $output
}

Set-Location -LiteralPath $RepoRoot
$governanceScript = Join-Path $RepoRoot 'tools\governance.ps1'

# Execution
Write-Host "Running readiness publish..."
Invoke-Git -Arguments @('fetch', '--prune', $Remote)
$currentBranch = Get-GitOutput -Arguments @('branch', '--show-current')
if ($currentBranch -ne $ExpectedBranch) { throw "Wrong branch!" }

Invoke-GovernanceValidateIsolated -WorkingDirectory $RepoRoot -ScriptPath $governanceScript
Invoke-Git -Arguments @('push', '--set-upstream', $Remote, $ExpectedBranch)

$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($null -ne $gh) {
    $existingPr = & gh pr list --head $ExpectedBranch --base $BaseBranch --state open --json url --jq '.[0].url'
    if (-not [string]::IsNullOrWhiteSpace($existingPr)) {
        Write-Host "PR already exists: $existingPr"
    } else {
        $prBody = "Materialize and record the current commercial-readiness NO-GO decision."
        $createdPr = & gh pr create --base $BaseBranch --head $ExpectedBranch --title $PrTitle --body $prBody
        Write-Host "Created PR: $createdPr"
    }
}
Write-Host "Done."
