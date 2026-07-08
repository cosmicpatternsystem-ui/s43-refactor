[CmdletBinding()]
param(
    [string]$RepoRoot
)

$ErrorActionPreference = 'Stop'

function Resolve-RoadmapValidator {
    param(
        [Parameter(Mandatory=$true)]
        [string]$RepoRoot
    )

    $candidates = @(
        (Join-Path $RepoRoot 'validate-roadmap.ps1'),
        (Join-Path $RepoRoot 'scripts\validate-roadmap.ps1'),
        (Join-Path $RepoRoot 'scripts\test-roadmap.ps1')
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }

    throw "Missing validator. Checked: $($candidates -join '; ')"
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
        $RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
    }
    else {
        $RepoRoot = (Get-Location).Path
    }
}

$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
$scriptBase = Join-Path $RepoRoot 'scripts'

Write-Host "== ASO-X Durability Verification ==" -ForegroundColor Cyan

$encodingTest = Join-Path $scriptBase 'Test-EncodingPolicy.ps1'
$repoHygieneTest = Join-Path $scriptBase 'Test-RepoHygiene.ps1'
$journalTest = Join-Path $RepoRoot 'tests\powershell\test-write-journal.ps1'
$atomicTest = Join-Path $RepoRoot 'tests\powershell\test-write-atomic-json.ps1'
$roadmapValidator = Resolve-RoadmapValidator -RepoRoot $RepoRoot

& $encodingTest -RepoRoot $RepoRoot
& $repoHygieneTest -RepoRoot $RepoRoot
& $journalTest -RepoRoot $RepoRoot
& $atomicTest -RepoRoot $RepoRoot

& powershell -NoProfile -ExecutionPolicy Bypass -File $roadmapValidator
if ($LASTEXITCODE -ne 0) {
    throw ("Roadmap validator failed with exit code {0}: {1}" -f $LASTEXITCODE, $roadmapValidator)
}

Write-Host "[OK] Durability verification passed" -ForegroundColor Green
