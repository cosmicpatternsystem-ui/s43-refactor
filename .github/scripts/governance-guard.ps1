param(
    [string]$RepoRoot = (Resolve-Path ".").Path
)
$ErrorActionPreference = "Stop"

function Fail([int]$Code, [string]$Message) {
    Write-Host $Message
    exit $Code
}

$canonical = Join-Path $RepoRoot "docs/governance/ROADMAP_CURRENT.json"
$manifest = Join-Path $RepoRoot "docs/governance/GOVERNANCE_DOCUMENTS_MANIFEST.json"
$expected = @(
    "docs/governance/ROADMAP_CURRENT.json",
    "docs/governance/ROADMAP_CANONICAL.md",
    "docs/governance/DECISION_MATRIX.json",
    "docs/governance/DECISION_MATRIX.md",
    "repo/policies/artifactretention.policy.json",
    "repo/policies/merge-safety.policy.json",
    "repo/policies/evidencerecord.policy.json"
)

if (-not (Test-Path $canonical)) { Fail 101 "canonical roadmap missing" }
if (-not (Test-Path $manifest)) { Fail 102 "canonical manifest missing" }

try {
    $json = Get-Content $canonical -Raw -Encoding utf8 | ConvertFrom-Json
} catch {
    Fail 103 "invalid roadmap JSON"
}

$shadowPaths = @(
    "config/roadmap.json",
    "repo/roadmap/roadmap.yaml",
    "docs/roadmap/roadmap.yaml"
)

foreach ($p in $shadowPaths) {
    if (Test-Path (Join-Path $RepoRoot $p)) {
        Fail 201 "unauthorized shadow copy detected: $p"
    }
}

try {
    $manifestJson = Get-Content $manifest -Raw -Encoding utf8 | ConvertFrom-Json
} catch {
    Fail 102 "invalid manifest JSON"
}

$missing = @()
foreach ($p in $expected) {
    if (-not (Test-Path (Join-Path $RepoRoot $p))) { $missing += $p }
}
if ($missing.Count -gt 0) {
    Fail 102 ("canonical manifest missing entries or files absent: " + ($missing -join ", "))
}

Write-Host "integrity verified"
exit 0