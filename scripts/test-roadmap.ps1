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

Invoke-Step "Assert Depends On header metadata is generated" {
  $roadmap = Get-Content -Raw "ROADMAP_CURRENT.json" | ConvertFrom-Json
  $phase = @($roadmap.phases) | Where-Object { $_.file -eq "PHASE_42_05_DEPENDS_ON_HEADER_PARSING_HARDENING.md" } | Select-Object -First 1

  if ($null -eq $phase) {
    throw "PHASE_42_05_DEPENDS_ON_HEADER_PARSING_HARDENING.md not found in ROADMAP_CURRENT.json."
  }

  if (@($phase.depends_on) -notcontains "PHASE_42_04_ROADMAP_METADATA_REGRESSION_GUARD.md") {
    throw "Depends On header was not generated into depends_on for PHASE_42_05."
  }
}

Invoke-Step "Assert generated roadmap is committed" {
  git diff --exit-code -- ROADMAP_CURRENT.json
  if ($LASTEXITCODE -ne 0) {
    throw "Generated ROADMAP_CURRENT.json has uncommitted changes. Run scripts/update-roadmap.ps1 and commit the result."
  }
}

Invoke-Step "Ignore empty Depends On header value" {
  $tempEmptyDependsPhasePath = Join-Path $PSScriptRoot ".." "PHASE_99_98_TEMP_EMPTY_DEPENDS_ON_HEADER.md"
  $emptyDependsRoadmapPath = Join-Path $PSScriptRoot ".." "ROADMAP_CURRENT.json"
  $emptyDependsUpdatePath = Join-Path $PSScriptRoot "update-roadmap.ps1"
  $originalEmptyDependsRoadmapBytes = [System.IO.File]::ReadAllBytes($emptyDependsRoadmapPath)

  try {
    @(
      "# PHASE 99.98 TEMP EMPTY DEPENDS ON HEADER"
      ""
      "Status: Proposed"
      "Documentation Only: Yes"
      "Owner: Operations / Governance"
      "Priority: High"
      "Depends On:"
      ""
      "## Summary"
      "Temporary regression fixture for empty Depends On header parsing."
    ) | Set-Content -Path $tempEmptyDependsPhasePath

    & $emptyDependsUpdatePath | Out-Null

    $roadmap = Get-Content -Raw -Path $emptyDependsRoadmapPath | ConvertFrom-Json
    $phase = $roadmap.phases | Where-Object { $_.file -eq "PHASE_99_98_TEMP_EMPTY_DEPENDS_ON_HEADER.md" }

    if (-not $phase) {
      throw "Temporary empty Depends On phase was not generated into ROADMAP_CURRENT.json."
    }

    if (@($phase.depends_on).Count -ne 0) {
      throw "Empty Depends On header produced unexpected dependencies: $($phase.depends_on -join ', ')"
    }
  }
  finally {
    if (Test-Path $tempEmptyDependsPhasePath) {
      Remove-Item $tempEmptyDependsPhasePath -Force
    }

    [System.IO.File]::WriteAllBytes($emptyDependsRoadmapPath, $originalEmptyDependsRoadmapBytes)
  }
}

Invoke-Step "Resolve human-readable Depends On header label" {
  $tempLabelDependsPhasePath = Join-Path $PSScriptRoot ".." "PHASE_99_97_TEMP_LABEL_DEPENDS_ON_HEADER.md"
  $labelDependsRoadmapPath = Join-Path $PSScriptRoot ".." "ROADMAP_CURRENT.json"
  $labelDependsUpdatePath = Join-Path $PSScriptRoot "update-roadmap.ps1"
  $expectedDependsOn = "PHASE_42_04_ROADMAP_METADATA_REGRESSION_GUARD.md"
  $originalLabelDependsRoadmapBytes = [System.IO.File]::ReadAllBytes($labelDependsRoadmapPath)

  try {
    @(
      "# PHASE 99.97 TEMP LABEL DEPENDS ON HEADER"
      ""
      "Status: Proposed"
      "Documentation Only: Yes"
      "Owner: Operations / Governance"
      "Priority: High"
      "Depends On: Phase 42.04"
      ""
      "## Summary"
      "Temporary regression fixture for human-readable Depends On label resolution."
    ) | Set-Content -Path $tempLabelDependsPhasePath -Encoding utf8

    & $labelDependsUpdatePath | Out-Null

    $roadmap = Get-Content -Raw -Path $labelDependsRoadmapPath | ConvertFrom-Json
    $phase = $roadmap.phases | Where-Object { $_.file -eq "PHASE_99_97_TEMP_LABEL_DEPENDS_ON_HEADER.md" }

    if (-not $phase) {
      throw "Temporary label Depends On phase was not generated into ROADMAP_CURRENT.json."
    }

    $actualDependsOn = @($phase.depends_on)

    if ($actualDependsOn.Count -ne 1 -or $actualDependsOn[0] -ne $expectedDependsOn) {
      throw "Human-readable Depends On header was not resolved to $expectedDependsOn. Actual: $($actualDependsOn -join ', ')"
    }
  }
  finally {
    if (Test-Path $tempLabelDependsPhasePath) {
      Remove-Item $tempLabelDependsPhasePath -Force
    }

    [System.IO.File]::WriteAllBytes($labelDependsRoadmapPath, $originalLabelDependsRoadmapBytes)
  }
}

Invoke-Step "Reject missing Depends On header target" {
  $tempDependsPhasePath = Join-Path $PSScriptRoot ".." "PHASE_99_99_TEMP_MISSING_DEPENDS_ON_HEADER_TARGET.md"
  $dependsRoadmapPath = Join-Path $PSScriptRoot ".." "ROADMAP_CURRENT.json"
  $dependsUpdatePath = Join-Path $PSScriptRoot "update-roadmap.ps1"
  $dependsValidatorPath = Join-Path $PSScriptRoot "validate-roadmap.ps1"
  $originalDependsRoadmapBytes = [System.IO.File]::ReadAllBytes($dependsRoadmapPath)

  try {
    @'
# PHASE 99.99 TEMP MISSING DEPENDS ON HEADER TARGET

Status: Proposed
Documentation Only: Yes
Owner: Operations / Governance
Priority: High
Depends On: PHASE_DOES_NOT_EXIST.md

## Summary
Temporary negative test fixture. This file must be removed by the test.
'@ | Set-Content -Path $tempDependsPhasePath -NoNewline

    & $dependsUpdatePath | Out-Null
    $validatorRejectedMissingDependency = $false
    try {
      & $dependsValidatorPath *> $null
    }
    catch {
      $validatorRejectedMissingDependency = $true
    }

    if (-not $validatorRejectedMissingDependency -and $LASTEXITCODE -eq 0) {
      throw "Validator accepted a missing Depends On header target."
    }
  }
  finally {
    if (Test-Path $tempDependsPhasePath) {
      Remove-Item $tempDependsPhasePath -Force
    }

    [System.IO.File]::WriteAllBytes($dependsRoadmapPath, $originalDependsRoadmapBytes)
  }
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

function Invoke-ExpectedRoadmapValidationFailure {
    param(
        [Parameter(Mandatory = $true)]
        [string] $StepName,

        [Parameter(Mandatory = $true)]
        [scriptblock] $MutateRoadmap
    )

    Write-Host "==> $StepName"

    $roadmapPath = Join-Path $repoRoot "ROADMAP_CURRENT.json"
    $originalRoadmapBytes = [System.IO.File]::ReadAllBytes($roadmapPath)

    try {
        $roadmap = Get-Content -Raw $roadmapPath | ConvertFrom-Json
        & $MutateRoadmap $roadmap
        $roadmap | ConvertTo-Json -Depth 20 | Set-Content -Path $roadmapPath -Encoding utf8BOM

        & pwsh -NoProfile -File (Join-Path $repoRoot "scripts/validate-roadmap.ps1") *> $null

        if ($LASTEXITCODE -eq 0) {
            throw "Expected roadmap validator to reject: $StepName"
        }

        $global:LASTEXITCODE = 0
        Write-Host "OK: $StepName"
    }
    finally {
        [System.IO.File]::WriteAllBytes($roadmapPath, $originalRoadmapBytes)
    }
}

Invoke-ExpectedRoadmapValidationFailure -StepName "Reject invalid roadmap phase status" -MutateRoadmap {
    param($Roadmap)

    $Roadmap.phases[0].status = "__INVALID_STATUS__"
}

Invoke-ExpectedRoadmapValidationFailure -StepName "Reject invalid roadmap phase priority" -MutateRoadmap {
    param($Roadmap)

    $Roadmap.phases[0].priority = "__INVALID_PRIORITY__"
}

Write-Host "Operational roadmap smoke test passed."


