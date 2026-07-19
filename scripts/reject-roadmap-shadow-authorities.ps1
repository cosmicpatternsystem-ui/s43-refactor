$ErrorActionPreference = "Stop"

$shadowPaths = @(
    "ROADMAP_CURRENT.json",
    "ROADMAP_CANONICAL.md",
    "ROADMAP/ROADMAP_STATE.json",
    "ROADMAP/ROADMAP_CANONICAL.md",
    "AUDIT/ROADMAP_CURRENT.json",
    "AUDIT/ROADMAP_CURRENT.md"
)

$found = @()
foreach ($path in $shadowPaths) {
    if (Test-Path -LiteralPath $path) {
        $found += $path
    }
}

if ($found.Count -gt 0) {
    foreach ($path in $found) {
        Write-Host "::error::forbidden roadmap shadow exists: $path"
    }
    exit 1
}

Write-Host "No forbidden roadmap shadow authorities found."