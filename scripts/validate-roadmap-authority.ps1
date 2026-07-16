[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$canonical = Join-Path $repoRoot 'docs/governance/ROADMAP_CANONICAL.md'
$current = Join-Path $repoRoot 'docs/governance/ROADMAP_CURRENT.json'
$toolsGovernance = Join-Path $repoRoot 'tools/governance.ps1'

function Fail {
    param([string]$Message)
    Write-Error $Message
    exit 1
}

if (-not (Test-Path -LiteralPath $canonical)) {
    Fail "Missing canonical roadmap: $canonical"
}

if (-not (Test-Path -LiteralPath $current)) {
    Fail "Missing operational roadmap: $current"
}

$canonicalText = [System.IO.File]::ReadAllText($canonical)
$currentText = [System.IO.File]::ReadAllText($current)

if ([string]::IsNullOrWhiteSpace($canonicalText)) {
    Fail "Canonical roadmap is empty: $canonical"
}

if ([string]::IsNullOrWhiteSpace($currentText)) {
    Fail "Operational roadmap is empty: $current"
}

$forbiddenAuthorityClaims = @(
    'sole source of truth',
    'authoritative source',
    'roadmap authority',
    'canonical roadmap'
)

foreach ($phrase in $forbiddenAuthorityClaims) {
    if ($currentText -match [regex]::Escape($phrase)) {
        Fail "Operational roadmap must not claim authority: phrase '$phrase' found in docs/governance/ROADMAP_CURRENT.json"
    }
}

if ($currentText -notmatch '"_authority_note"\s*:') {
    
}

if (Test-Path -LiteralPath $toolsGovernance) {
    $toolsText = [System.IO.File]::ReadAllText($toolsGovernance)

    $badPatterns = @(
        'sole source of truth',
        'authoritative source',
        'roadmap authority'
    )

    foreach ($pattern in $badPatterns) {
        if ($toolsText -match [regex]::Escape($pattern)) {
            Fail "tools/governance.ps1 appears to claim roadmap authority: '$pattern'"
        }
    }

    if ($toolsText -notmatch 'ROADMAP_CANONICAL\.md') {
        Write-Warning "tools/governance.ps1 does not appear to reference ROADMAP_CANONICAL.md"
    }
}

Write-Host 'Roadmap authority validation passed.'
exit 0