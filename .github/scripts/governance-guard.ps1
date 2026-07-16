param(
    [string]$RepoRoot = (Resolve-Path ".").Path
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Fail {
    param(
        [int]$Code,
        [string]$Message
    )
    Write-Error $Message
    exit $Code
}

$validatorPath = Join-Path $RepoRoot 'scripts/validate-roadmap-authority.ps1'
if (-not (Test-Path -LiteralPath $validatorPath)) {
    Fail 104 'roadmap authority validator missing'
}

& $validatorPath
if ($LASTEXITCODE -ne 0) {
    throw 'Roadmap authority validation failed.'
}

$canonical = Join-Path $RepoRoot 'docs/governance/ROADMAP_CURRENT.json'
if (-not (Test-Path -LiteralPath $canonical)) {
    Fail 101 'canonical roadmap missing'
}

try {
    $json = Get-Content -LiteralPath $canonical -Raw -Encoding utf8 | ConvertFrom-Json
} catch {
    Fail 103 'invalid roadmap JSON'
}

$shadowPaths = @(
    'config/roadmap.json',
    'repo/roadmap/roadmap.yaml',
    'docs/roadmap/roadmap.yaml'
)

foreach ($p in $shadowPaths) {
    $full = Join-Path $RepoRoot $p
    if (Test-Path -LiteralPath $full) {
        Fail 201 "unauthorized shadow copy detected: $p"
    }
}

$expected = @(
    'docs/governance/ROADMAP_CANONICAL.md',
    'docs/governance/ROADMAP_CURRENT.json',
    'scripts/update-roadmap.ps1',
    'scripts/validate-roadmap.ps1',
    'scripts/validate-roadmap-authority.ps1',
    'scripts/verify-roadmap-smoke.ps1',
    'scripts/roadmap_guard.py',
    'tools/governance.ps1'
)

$missing = @()
foreach ($p in $expected) {
    $full = Join-Path $RepoRoot $p
    if (-not (Test-Path -LiteralPath $full)) {
        $missing += $p
    }
}

if ($missing.Count -gt 0) {
    Fail 102 ('required governance files missing: ' + ($missing -join ', '))
}

$manifest = Join-Path $RepoRoot 'docs/governance/ROADMAP_MANIFEST.json'
if (Test-Path -LiteralPath $manifest) {
    try {
        $manifestJson = Get-Content -LiteralPath $manifest -Raw -Encoding utf8 | ConvertFrom-Json
        Write-Host 'manifest detected and parsed'
    } catch {
        Fail 105 'invalid manifest JSON'
    }
}
else {
    Write-Warning 'ROADMAP_MANIFEST.json not found; manifest validation skipped during migration.'
}

Write-Host 'integrity verified'
exit 0