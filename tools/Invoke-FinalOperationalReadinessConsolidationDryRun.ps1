[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Test-AuditEvidenceForPhase {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PhaseNumber
    )

    if (-not (Test-Path 'AUDIT')) {
        return $false
    }

    $phaseMarker = "PHASE$PhaseNumber"

    $auditMatches = Get-ChildItem -Path 'AUDIT' -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -like "*$phaseMarker*" -or
            $_.FullName -like "*$phaseMarker*"
        }

    if (@($auditMatches).Count -gt 0) {
        return $true
    }

    $gitLogMatches = git log --oneline --all -- 2>$null |
        Where-Object {
            $_ -like "*phase $([int]$PhaseNumber)*" -or
            $_ -like "*Phase $([int]$PhaseNumber)*" -or
            $_ -like "*PHASE$PhaseNumber*" -or
            $_ -like "*phase$PhaseNumber*"
        }

    return @($gitLogMatches).Count -gt 0
}

$missing = New-Object System.Collections.Generic.List[string]

if (-not (Test-Path 'AUDIT')) { $missing.Add('AUDIT root') }
if (-not (Test-Path 'tools')) { $missing.Add('tools root') }

$requiredPhases = @(
    '23',
    '24',
    '25',
    '26',
    '27',
    '28',
    '29',
    '30'
)

foreach ($phase in $requiredPhases) {
    if (-not (Test-AuditEvidenceForPhase -PhaseNumber $phase)) {
        $missing.Add("PHASE$phase evidence")
    }
}

if (@($missing).Count -gt 0) {
    Write-Host 'P31_DRY_RUN_FAIL'
    Write-Host 'Missing evidence:'
    $missing | ForEach-Object { Write-Host "- $_" }
    exit 1
}

Write-Host 'P31_DRY_RUN_PASS'
exit 0
