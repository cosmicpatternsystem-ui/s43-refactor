[CmdletBinding()]
param(
    [string]$RepoRoot,
    [switch]$KeepArtifacts
)

$ErrorActionPreference = 'Stop'

function Get-JournalSnapshot {
    param(
        [Parameter(Mandatory=$true)]
        [string]$JournalRoot
    )

    $map = @{}

    if (-not (Test-Path -LiteralPath $JournalRoot)) {
        return $map
    }

    $files = @(Get-ChildItem -LiteralPath $JournalRoot -Filter '*.jsonl' -File -Recurse -ErrorAction SilentlyContinue)
    foreach ($file in $files) {
        $count = @(Get-Content -LiteralPath $file.FullName -ErrorAction Stop).Count
        $map[$file.FullName] = $count
    }

    return $map
}

function Get-NewJournalEntries {
    param(
        [Parameter(Mandatory=$true)]
        [string]$JournalRoot,

        [Parameter(Mandatory=$true)]
        [hashtable]$Before
    )

    $entries = New-Object System.Collections.Generic.List[object]

    if (-not (Test-Path -LiteralPath $JournalRoot)) {
        return $entries
    }

    $files = @(Get-ChildItem -LiteralPath $JournalRoot -Filter '*.jsonl' -File -Recurse -ErrorAction SilentlyContinue)
    foreach ($file in $files) {
        $beforeCount = 0
        if ($Before.ContainsKey($file.FullName)) {
            $beforeCount = [int]$Before[$file.FullName]
        }

        $lines = @(Get-Content -LiteralPath $file.FullName -ErrorAction Stop)
        if ($lines.Count -le $beforeCount) {
            continue
        }

        for ($i = $beforeCount; $i -lt $lines.Count; $i++) {
            $line = $lines[$i]
            if ([string]::IsNullOrWhiteSpace($line)) {
                continue
            }

            $entries.Add(($line | ConvertFrom-Json)) | Out-Null
        }
    }

    return $entries
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
        $RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
    }
    else {
        $RepoRoot = (Get-Location).Path
    }
}

$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
$scriptPath = Join-Path $RepoRoot 'scripts\Write-AtomicJson.ps1'

if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "Missing script: $scriptPath"
}

$testRoot = Join-Path $RepoRoot 'runtime\tests\atomic'
if (Test-Path -LiteralPath $testRoot) {
    Remove-Item -LiteralPath $testRoot -Recurse -Force
}
[System.IO.Directory]::CreateDirectory($testRoot) | Out-Null

$journalRoot = Join-Path $RepoRoot 'data\journal'
$beforeJournal = Get-JournalSnapshot -JournalRoot $journalRoot

$runId = 'durability_atomic_' + ([System.Guid]::NewGuid().ToString('N'))
$testPassed = $false

try {
    Push-Location $testRoot
    try {
        $target = '.\state.json'

        $validJson = @"
{
  "generated_by": "tests/powershell/test-write-atomic-json.ps1",
  "run_id": "$runId",
  "version": 1,
  "value": "good"
}
"@

        & $scriptPath `
            -Path $target `
            -Content $validJson `
            -Operation 'checkpoint' `
            -Phase 'durability_verification'

        if (-not (Test-Path -LiteralPath $target)) {
            throw "Atomic write did not create target file"
        }

        $firstRaw = Get-Content -LiteralPath $target -Raw -Encoding UTF8
        $first = $firstRaw | ConvertFrom-Json

        if ($first.value -ne 'good') {
            throw "Unexpected value after successful atomic write"
        }

        if ($first.run_id -ne $runId) {
            throw "Unexpected run_id after successful atomic write"
        }

        $invalidJson = '{ "generated_by": "tests/powershell/test-write-atomic-json.ps1", "run_id": "' + $runId + '", "broken": ]'
        $failed = $false

        try {
            & $scriptPath `
                -Path $target `
                -Content $invalidJson `
                -Operation 'checkpoint' `
                -Phase 'durability_verification'
        }
        catch {
            $failed = $true
        }

        if (-not $failed) {
            throw "Invalid JSON test was expected to fail"
        }

        $secondRaw = Get-Content -LiteralPath $target -Raw -Encoding UTF8
        $second = $secondRaw | ConvertFrom-Json

        if ($second.value -ne 'good') {
            throw "Target file was corrupted after failed atomic write"
        }

        if ($second.run_id -ne $runId) {
            throw "Target file content changed unexpectedly after failed atomic write"
        }

        $tmpFiles = @(Get-ChildItem -LiteralPath $testRoot -Filter *.tmp -File -Recurse -ErrorAction SilentlyContinue)
        if ($tmpFiles.Count -ne 0) {
            throw "Temporary files leaked after atomic write failure"
        }
    }
    finally {
        Pop-Location
    }

    $newEntries = Get-NewJournalEntries -JournalRoot $journalRoot -Before $beforeJournal

    if ($newEntries.Count -lt 2) {
        throw "Expected at least 2 new journal entries, found $($newEntries.Count)"
    }

    $matchingEntries = @(
        $newEntries | Where-Object {
            $_.operation -eq 'checkpoint' -and
            $_.phase -eq 'durability_verification'
        }
    )

    if ($matchingEntries.Count -lt 2) {
        throw "Expected at least 2 matching journal entries for checkpoint/durability_verification, found $($matchingEntries.Count)"
    }

    $hasSuccess = $false
    $hasFailed = $false

    foreach ($entry in $matchingEntries) {
        if ($entry.status -eq 'success') {
            $hasSuccess = $true
        }
        elseif ($entry.status -eq 'failed') {
            $hasFailed = $true
        }
    }

    if (-not $hasSuccess) {
        throw "Expected a success status entry in new journal entries"
    }

    if (-not $hasFailed) {
        throw "Expected a failed status entry in new journal entries"
    }

    $testPassed = $true
    Write-Host "[OK] Atomic JSON durability test passed" -ForegroundColor Green
}
finally {
    if ($testPassed -and -not $KeepArtifacts) {
        $runtimeTestsRoot = Join-Path $RepoRoot 'runtime\tests'
        if (Test-Path -LiteralPath $runtimeTestsRoot) {
            Remove-Item -LiteralPath $runtimeTestsRoot -Recurse -Force
        }
    }
}
