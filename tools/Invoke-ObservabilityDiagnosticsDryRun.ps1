param(
    [string]$AuditPath
)

$ErrorActionPreference = "Stop"

if (-not $AuditPath) {
    throw "AuditPath is required."
}

Write-Host "PHASE26_OBSERVABILITY_DRY_RUN_START"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$observabilityKeywords = @(
    "logging",
    "logger",
    "loguru",
    "trace",
    "metric",
    "metrics",
    "health",
    "readiness",
    "liveness",
    "diagnostic",
    "telemetry",
    "exception",
    "support"
)

$detectedFiles = @()
$keywordHits = @()

if (Get-Command rg -ErrorAction SilentlyContinue) {
    foreach ($keyword in $observabilityKeywords) {
        $hits = rg -n -i --glob "!AUDIT/**" --glob "!*.md" --glob "!*.txt" $keyword . 2>$null
        if ($hits) {
            $keywordHits += "### $keyword"
            $keywordHits += $hits | Select-Object -First 50
        }
    }

    $detectedFiles = rg --files | rg -i "log|logger|observability|diagnostic|health|metric|telemetry|support"
} else {
    $files = Get-ChildItem -Recurse -File | Where-Object {
        $_.FullName -notmatch "\\AUDIT\\" -and
        $_.Extension -notin @(".md", ".txt")
    }

    foreach ($file in $files) {
        $content = Get-Content -Path $file.FullName -ErrorAction SilentlyContinue
        foreach ($keyword in $observabilityKeywords) {
            if ($content -match $keyword) {
                $keywordHits += "$($file.FullName): $keyword"
            }
        }
    }

    $detectedFiles = Get-ChildItem -Recurse -File | Where-Object {
        $_.Name -match "log|logger|observability|diagnostic|health|metric|telemetry|support"
    } | ForEach-Object { $_.FullName.Replace($repoRoot + "\", "") }
}

Add-Content -Path $AuditPath -Value ""
Add-Content -Path $AuditPath -Value "## Detected Observability-related Files"
if (-not $detectedFiles -or $detectedFiles.Count -eq 0) {
    Add-Content -Path $AuditPath -Value "- none detected automatically"
} else {
    $detectedFiles | Select-Object -First 200 | ForEach-Object {
        Add-Content -Path $AuditPath -Value "- $_"
    }
}

Add-Content -Path $AuditPath -Value ""
Add-Content -Path $AuditPath -Value "## Keyword Hit Summary"
if (-not $keywordHits -or $keywordHits.Count -eq 0) {
    Add-Content -Path $AuditPath -Value "- no keyword hits detected automatically"
} else {
    $keywordHits | Select-Object -First 300 | ForEach-Object {
        Add-Content -Path $AuditPath -Value "$_"
    }
}

Write-Host "PHASE26_OBSERVABILITY_DRY_RUN_PASS"
