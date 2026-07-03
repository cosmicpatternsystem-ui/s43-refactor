[CmdletBinding()]
param(
    [string]$RepoRoot
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
        $RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
    }
    else {
        $RepoRoot = (Get-Location).Path
    }
}

$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
$scriptPath = Join-Path $RepoRoot 'scripts\Write-Journal.ps1'

if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "Missing script: $scriptPath"
}

$journalRoot = Join-Path $RepoRoot 'data\journal'
$runId = 'durability_test_' + ([System.Guid]::NewGuid().ToString('N'))

$jobs = @()
1..10 | ForEach-Object {
    $n = $_
    $jobs += Start-Job -ScriptBlock {
        param($RepoRootInner, $RunIdInner, $NInner)

        $scriptInner = Join-Path $RepoRootInner 'scripts\Write-Journal.ps1'
        $suffix = '{0}_{1:00}' -f $RunIdInner, $NInner

        & $scriptInner `
            -Phase 'durability_verification' `
            -Operation 'checkpoint' `
            -OldStateHash ('old_' + $suffix) `
            -NewStateHash ('new_' + $suffix) `
            -Status 'success' `
            -DurationMs $NInner
    } -ArgumentList $RepoRoot, $runId, $n
}

$jobs | Wait-Job | Out-Null

$failed = @($jobs | Where-Object { $_.State -ne 'Completed' })
if ($failed.Count -gt 0) {
    $failed | Receive-Job -Keep | Out-Host
    throw "One or more journal jobs failed"
}

$jobs | Receive-Job | Out-Null
$jobs | Remove-Job -Force | Out-Null

if (-not (Test-Path -LiteralPath $journalRoot)) {
    throw "Journal root was not created: $journalRoot"
}

$files = @(Get-ChildItem -LiteralPath $journalRoot -Filter '*.jsonl' -File -Recurse)
if ($files.Count -lt 1) {
    throw "Expected at least one journal file under $journalRoot"
}

$matched = New-Object System.Collections.Generic.List[object]

foreach ($file in $files) {
    $lines = @(Get-Content -LiteralPath $file.FullName)
    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        if ($line -notlike "*$runId*") {
            continue
        }

        $obj = $line | ConvertFrom-Json

        if ($obj.operation -ne 'checkpoint') {
            throw "Unexpected journal operation in $($file.FullName): $($obj.operation)"
        }

        if ($obj.phase -ne 'durability_verification') {
            throw "Unexpected journal phase in $($file.FullName): $($obj.phase)"
        }

        if ($obj.status -ne 'success') {
            throw "Unexpected journal status in $($file.FullName): $($obj.status)"
        }

        if ([string]::IsNullOrWhiteSpace([string]$obj.old_state_hash)) {
            throw "Journal line missing old_state_hash in $($file.FullName)"
        }

        if ([string]::IsNullOrWhiteSpace([string]$obj.new_state_hash)) {
            throw "Journal line missing new_state_hash in $($file.FullName)"
        }

        if ([string]$obj.old_state_hash -notlike "old_$runId*") {
            throw "Journal line old_state_hash did not match run id: $($obj.old_state_hash)"
        }

        if ([string]$obj.new_state_hash -notlike "new_$runId*") {
            throw "Journal line new_state_hash did not match run id: $($obj.new_state_hash)"
        }

        $matched.Add($obj) | Out-Null
    }
}

if ($matched.Count -ne 10) {
    throw "Expected 10 journal lines for run $runId, found $($matched.Count)"
}

Write-Host "[OK] Journal durability test passed" -ForegroundColor Green
