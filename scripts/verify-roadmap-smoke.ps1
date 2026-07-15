$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

& powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\update-roadmap.ps1"
if ($LASTEXITCODE -ne 0) {
    throw "update-roadmap.ps1 failed with exit code $LASTEXITCODE"
}

$roadmapPath = Join-Path $repoRoot "docs\governance\ROADMAP_CURRENT.json"
if (-not (Test-Path $roadmapPath)) {
    throw "ROADMAP_CURRENT.json not found at $roadmapPath"
}

$raw = Get-Content -Raw $roadmapPath
$roadmap = $raw | ConvertFrom-Json

$props = @($roadmap.PSObject.Properties.Name)

if ($props.Count -eq 0) {
    throw "ROADMAP_CURRENT.json parsed but has no top-level properties"
}

$phaseLikeProperty = $null
foreach ($candidate in @("phases", "items", "initiatives")) {
    if ($props -contains $candidate) {
        $phaseLikeProperty = $candidate
        break
    }
}

if (-not $phaseLikeProperty) {
    throw ("ROADMAP_CURRENT.json missing expected collection property. Found: " + ($props -join ", "))
}

$entries = @($roadmap.$phaseLikeProperty)
if ($entries.Count -eq 0) {
    throw "ROADMAP_CURRENT.json property '$phaseLikeProperty' is empty"
}

if (($props -contains "phase_count") -and ($phaseLikeProperty -eq "phases")) {
    if ([int]$roadmap.phase_count -ne $entries.Count) {
        throw "phase_count ($($roadmap.phase_count)) does not match phases count ($($entries.Count))"
    }
}

Write-Host "[OK] roadmap smoke test passed"
Write-Host ("[INFO] validated property: " + $phaseLikeProperty)
Write-Host ("[INFO] entry count: " + $entries.Count)