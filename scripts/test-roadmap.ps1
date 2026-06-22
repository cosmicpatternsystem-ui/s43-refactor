param(
  [switch]$SkipUpdate
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Invoke-Step {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Name,

    [Parameter(Mandatory = $true)]
    [scriptblock]$Command
  )

  Write-Host "==> $Name"
  & $Command
  Write-Host "OK: $Name"
}

if (-not (Test-Path "ROADMAP_CURRENT.json")) {
  throw "ROADMAP_CURRENT.json not found."
}

if (-not (Test-Path "scripts/update-roadmap.ps1")) {
  throw "scripts/update-roadmap.ps1 not found."
}

if (-not (Test-Path "scripts/validate-roadmap.ps1")) {
  throw "scripts/validate-roadmap.ps1 not found."
}

if (-not $SkipUpdate) {
  Invoke-Step "Regenerate operational roadmap" {
    & "scripts/update-roadmap.ps1"
  }
}

Invoke-Step "Validate operational roadmap" {
  & "scripts/validate-roadmap.ps1"
}

Invoke-Step "Assert generated roadmap is committed" {
  git diff --exit-code -- ROADMAP_CURRENT.json
}

Write-Host "==> Reject missing roadmap dependency"
$roadmapPath = Join-Path $PSScriptRoot ".." "ROADMAP_CURRENT.json"
$validatorPath = Join-Path $PSScriptRoot "validate-roadmap.ps1"
$originalRoadmapBytes = [System.IO.File]::ReadAllBytes($roadmapPath)

try {
    $roadmapJson = [System.Text.Encoding]::UTF8.GetString($originalRoadmapBytes)
    $roadmap = $roadmapJson | ConvertFrom-Json

    if (@($roadmap.phases).Count -lt 1) {
        throw "Cannot run dependency regression without at least one roadmap phase."
    }

    $roadmap.phases[0].depends_on = @("__MISSING_ROADMAP_PHASE__.md")
    $mutatedRoadmapJson = ($roadmap | ConvertTo-Json -Depth 20) + "`n"
    [System.IO.File]::WriteAllText($roadmapPath, $mutatedRoadmapJson, [System.Text.UTF8Encoding]::new($false))

    & pwsh -NoProfile -File $validatorPath *> $null

    if ($LASTEXITCODE -eq 0) {
        throw "Expected roadmap validator to reject a missing dependency reference."
    }

    $global:LASTEXITCODE = 0
    Write-Host "OK: Reject missing roadmap dependency"
}
finally {
    [System.IO.File]::WriteAllBytes($roadmapPath, $originalRoadmapBytes)
}

Write-Host "Operational roadmap smoke test passed."

