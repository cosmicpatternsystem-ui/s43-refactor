$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$journalDir = Join-Path $repoRoot "data\journal"
$beforeJournal = @{}
if (Test-Path $journalDir) {
    Get-ChildItem -LiteralPath $journalDir -File | ForEach-Object {
        $beforeJournal[$_.FullName] = $_.LastWriteTimeUtc
    }
}

try {
    & powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\update-roadmap.ps1"
    if ($LASTEXITCODE -ne 0) {
        throw "update-roadmap.ps1 failed with exit code $LASTEXITCODE"
    }

    $roadmapPath = Join-Path $repoRoot "docs\governance\ROADMAP_CURRENT.json"
    if (-not (Test-Path $roadmapPath)) {
        throw "ROADMAP_CURRENT.json not found at $roadmapPath"
    }

    $raw = Get-Content -Raw -LiteralPath $roadmapPath
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

    foreach ($requiredProp in @("phase_count", "updated_at_utc")) {
        if (-not ($props -contains $requiredProp)) {
            throw "ROADMAP_CURRENT.json missing required property '$requiredProp'"
        }
    }

    if ($phaseLikeProperty -eq "phases") {
        if ([int]$roadmap.phase_count -ne $entries.Count) {
            throw "phase_count ($($roadmap.phase_count)) does not match phases count ($($entries.Count))"
        }
    }

    $updatedAt = [string]$roadmap.updated_at_utc
    if ([string]::IsNullOrWhiteSpace($updatedAt)) {
        throw "updated_at_utc is empty"
    }

    if ($props -contains "canonical_roadmap") {
        $canonicalRoadmap = [string]$roadmap.canonical_roadmap
        if ([string]::IsNullOrWhiteSpace($canonicalRoadmap)) {
            throw "canonical_roadmap is present but empty"
        }
    }

    Write-Host "[OK] roadmap smoke test passed"
    Write-Host ("[INFO] validated property: " + $phaseLikeProperty)
    Write-Host ("[INFO] entry count: " + $entries.Count)
}
finally {
    if (Test-Path $journalDir) {
        $afterJournal = Get-ChildItem -LiteralPath $journalDir -File
        foreach ($fileInfo in $afterJournal) {
            if (-not $beforeJournal.ContainsKey($fileInfo.FullName)) {
                Remove-Item -LiteralPath $fileInfo.FullName -Force
                Write-Host ("[CLEANUP] removed generated journal artifact: " + $fileInfo.FullName)
            }
        }
    }
}
$validatorPath = Join-Path $PSScriptRoot 'validate-roadmap-authority.ps1'
& $validatorPath
if ($LASTEXITCODE -ne 0) {
    throw 'Smoke validation failed: roadmap authority.'
}
