param(
    [string]$AuditPath,
    [string]$ArtifactRoot = "dist"
)

$ErrorActionPreference = "Stop"

if (-not $AuditPath) {
    throw "AuditPath is required."
}

Write-Host "PHASE25_ARTIFACT_INTEGRITY_DRY_RUN_START"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$detectedPackagingSignals = @()

if (Test-Path ".\pyproject.toml") { $detectedPackagingSignals += "pyproject.toml" }
if (Test-Path ".\setup.py") { $detectedPackagingSignals += "setup.py" }
if (Test-Path ".\setup.cfg") { $detectedPackagingSignals += "setup.cfg" }
if (Test-Path ".\requirements.txt") { $detectedPackagingSignals += "requirements.txt" }
if (Test-Path ".\package.json") { $detectedPackagingSignals += "package.json" }
if (Test-Path ".\Dockerfile") { $detectedPackagingSignals += "Dockerfile" }

$artifactFiles = @()
if (Test-Path $ArtifactRoot) {
    $artifactFiles = Get-ChildItem -Path $ArtifactRoot -Recurse -File | ForEach-Object {
        $_.FullName.Replace($repoRoot + "\", "")
    }
}

$manifestPath = Join-Path $repoRoot "AUDIT/PHASE25_ARTIFACT_MANIFEST_DRY_RUN.txt"
$checksumPath = Join-Path $repoRoot "AUDIT/PHASE25_ARTIFACT_SHA256_DRY_RUN.txt"

if ($artifactFiles.Count -gt 0) {
    $artifactFiles | Sort-Object | Set-Content -Path $manifestPath

    $hashLines = foreach ($file in $artifactFiles) {
        $hash = Get-FileHash -Path $file -Algorithm SHA256
        "$($hash.Hash)  $file"
    }

    $hashLines | Set-Content -Path $checksumPath
} else {
    "NO_ARTIFACTS_DETECTED_IN_$ArtifactRoot" | Set-Content -Path $manifestPath
    "NO_ARTIFACTS_DETECTED_IN_$ArtifactRoot" | Set-Content -Path $checksumPath
}

Add-Content -Path $AuditPath -Value ""
Add-Content -Path $AuditPath -Value "## Detected Packaging Signals"
if ($detectedPackagingSignals.Count -eq 0) {
    Add-Content -Path $AuditPath -Value "- none detected automatically"
} else {
    $detectedPackagingSignals | ForEach-Object {
        Add-Content -Path $AuditPath -Value "- $_"
    }
}

Add-Content -Path $AuditPath -Value ""
Add-Content -Path $AuditPath -Value "## Artifact Dry-run Outputs"
Add-Content -Path $AuditPath -Value "- AUDIT/PHASE25_ARTIFACT_MANIFEST_DRY_RUN.txt"
Add-Content -Path $AuditPath -Value "- AUDIT/PHASE25_ARTIFACT_SHA256_DRY_RUN.txt"

Add-Content -Path $AuditPath -Value ""
Add-Content -Path $AuditPath -Value "## Artifact Detection Result"
if ($artifactFiles.Count -eq 0) {
    Add-Content -Path $AuditPath -Value "- no artifacts detected under $ArtifactRoot"
} else {
    Add-Content -Path $AuditPath -Value "- artifact count: $($artifactFiles.Count)"
}

Write-Host "PHASE25_ARTIFACT_INTEGRITY_DRY_RUN_PASS"
