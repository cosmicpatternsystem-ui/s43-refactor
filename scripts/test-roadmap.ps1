param (
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
        $tempEmptyDependsPhasePath = Join-Path (Join-Path $PSScriptRoot "..") "PHASE_99_98_TEMP_EMPTY_DEPENDS_ON_HEADER.md"
        $emptyDependsRoadmapPath = Join-Path (Join-Path $PSScriptRoot "..") "ROADMAP_CURRENT.json"
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
        $tempLabelDependsPhasePath = Join-Path (Join-Path $PSScriptRoot "..") "PHASE_99_97_TEMP_LABEL_DEPENDS_ON_HEADER.md"
        $labelDependsRoadmapPath = Join-Path (Join-Path $PSScriptRoot "..") "ROADMAP_CURRENT.json"
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

Invoke-Step "Resolve canonical filename Depends On header target" {
        $tempEmptyDependsPhasePath = Join-Path (Join-Path $PSScriptRoot "..") "PHASE_99_98_TEMP_EMPTY_DEPENDS_ON_HEADER.md"
        $emptyDependsRoadmapPath = Join-Path (Join-Path $PSScriptRoot "..") "ROADMAP_CURRENT.json"
  $filenameDependsUpdatePath = Join-Path $PSScriptRoot "update-roadmap.ps1"
  $expectedDependsOn = "PHASE_42_04_ROADMAP_METADATA_REGRESSION_GUARD.md"
  $originalFilenameDependsRoadmapBytes = [System.IO.File]::ReadAllBytes($filenameDependsRoadmapPath)

  try {
    @(
      "# PHASE 99.96 TEMP FILENAME DEPENDS ON HEADER"
      ""
      "Status: Proposed"
      "Documentation Only: Yes"
      "Owner: Operations / Governance"
      "Priority: High"
      "Depends On: PHASE_42_04_ROADMAP_METADATA_REGRESSION_GUARD.md"
      ""
      "## Summary"
      "Temporary regression fixture for canonical filename Depends On resolution."
    ) | Set-Content -Path $tempFilenameDependsPhasePath -Encoding utf8

    & $filenameDependsUpdatePath | Out-Null

    $roadmap = Get-Content -Raw -Path $filenameDependsRoadmapPath | ConvertFrom-Json
    $phase = $roadmap.phases | Where-Object { $_.file -eq "PHASE_99_96_TEMP_FILENAME_DEPENDS_ON_HEADER.md" }

    if (-not $phase) {
      throw "Temporary filename Depends On phase was not generated into ROADMAP_CURRENT.json."
    }

    $actualDependsOn = @($phase.depends_on)

    if ($actualDependsOn.Count -ne 1 -or $actualDependsOn[0] -ne $expectedDependsOn) {
      throw "Canonical filename Depends On header was not resolved to $expectedDependsOn. Actual: $($actualDependsOn -join ', ')"
    }
  }
  finally {
    if (Test-Path $tempFilenameDependsPhasePath) {
      Remove-Item $tempFilenameDependsPhasePath -Force
    }

    [System.IO.File]::WriteAllBytes($filenameDependsRoadmapPath, $originalFilenameDependsRoadmapBytes)
  }
Invoke-Step "Trim canonical filename Depends On header target" {
  $tempTrimmedFilenameDependsPhasePath = Join-Path (Join-Path $PSScriptRoot "..") "PHASE_99_95_TEMP_TRIMMED_FILENAME_DEPENDS_ON_HEADER.md"
  $trimmedFilenameDependsRoadmapPath = Join-Path (Join-Path $PSScriptRoot "..") "ROADMAP_CURRENT.json"
  $trimmedFilenameDependsUpdatePath = Join-Path $PSScriptRoot "update-roadmap.ps1"
  $expectedDependsOn = "PHASE_42_04_ROADMAP_METADATA_REGRESSION_GUARD.md"
  $originalTrimmedFilenameDependsRoadmapBytes = [System.IO.File]::ReadAllBytes($trimmedFilenameDependsRoadmapPath)

  try {
    @(
      "# PHASE 99.95 TEMP TRIMMED FILENAME DEPENDS ON HEADER"
      ""
      "Status: Proposed"
      "Documentation Only: Yes"
      "Owner: Operations / Governance"
      "Priority: High"
      "Depends On:   PHASE_42_04_ROADMAP_METADATA_REGRESSION_GUARD.md   "
      ""
      "## Summary"
      "Temporary regression fixture for trimmed canonical filename Depends On resolution."
    ) | Set-Content -Path $tempTrimmedFilenameDependsPhasePath -Encoding utf8

    & $trimmedFilenameDependsUpdatePath | Out-Null

    $roadmap = Get-Content -Raw -Path $trimmedFilenameDependsRoadmapPath | ConvertFrom-Json
    $phase = $roadmap.phases | Where-Object { $_.file -eq "PHASE_99_95_TEMP_TRIMMED_FILENAME_DEPENDS_ON_HEADER.md" }

    if (-not $phase) {
      throw "Temporary trimmed filename Depends On phase was not generated into ROADMAP_CURRENT.json."
    }

    $actualDependsOn = @($phase.depends_on)

    if ($actualDependsOn.Count -ne 1 -or $actualDependsOn[0] -ne $expectedDependsOn) {
      throw "Trimmed canonical filename Depends On header was not resolved to $expectedDependsOn. Actual: $($actualDependsOn -join ', ')"
    }
  }
  finally {
    if (Test-Path $tempTrimmedFilenameDependsPhasePath) {
      Remove-Item $tempTrimmedFilenameDependsPhasePath -Force
    }

    [System.IO.File]::WriteAllBytes($trimmedFilenameDependsRoadmapPath, $originalTrimmedFilenameDependsRoadmapBytes)
  }
Invoke-Step "Resolve mixed Depends On header targets" {
  $tempMixedDependsPhasePath = Join-Path (Join-Path $PSScriptRoot "..") "PHASE_99_94_TEMP_MIXED_DEPENDS_ON_HEADER.md"
  $mixedDependsRoadmapPath = Join-Path (Join-Path $PSScriptRoot "..") "ROADMAP_CURRENT.json"
  $mixedDependsUpdatePath = Join-Path $PSScriptRoot "update-roadmap.ps1"
  $expectedDependsOn = @(
    "PHASE_42_04_ROADMAP_METADATA_REGRESSION_GUARD.md"
    "PHASE_42_05_ROADMAP_REGRESSION_TESTING.md"
  )
  $originalMixedDependsRoadmapBytes = [System.IO.File]::ReadAllBytes($mixedDependsRoadmapPath)

  try {
    @(
      "# PHASE 99.94 TEMP MIXED DEPENDS ON HEADER"
      ""
      "Status: Proposed"
      "Documentation Only: Yes"
      "Owner: Operations / Governance"
      "Priority: High"
      "Depends On: Phase 42.04, PHASE_42_05_ROADMAP_REGRESSION_TESTING.md"
      ""
      "## Summary"
      "Temporary regression fixture for mixed Depends On header target resolution."
    ) | Set-Content -Path $tempMixedDependsPhasePath -Encoding utf8

    & $mixedDependsUpdatePath | Out-Null

    $roadmap = Get-Content -Raw -Path $mixedDependsRoadmapPath | ConvertFrom-Json
    $phase = $roadmap.phases | Where-Object { $_.file -eq "PHASE_99_94_TEMP_MIXED_DEPENDS_ON_HEADER.md" }

    if (-not $phase) {
      throw "Temporary mixed Depends On phase was not generated into ROADMAP_CURRENT.json."
    }

    $actualDependsOn = @($phase.depends_on)

    if ($actualDependsOn.Count -ne $expectedDependsOn.Count) {
      throw "Mixed Depends On header produced $($actualDependsOn.Count) dependencies, expected $($expectedDependsOn.Count). Actual: $($actualDependsOn -join ', ')"
    }

    for ($i = 0; $i -lt $expectedDependsOn.Count; $i++) {
      if ($actualDependsOn[$i] -ne $expectedDependsOn[$i]) {
        throw "Mixed Depends On header dependency mismatch at index $i. Expected: $($expectedDependsOn[$i]). Actual: $($actualDependsOn[$i])"
      }
    }
  }
  finally {
    if (Test-Path $tempMixedDependsPhasePath) {
      Remove-Item $tempMixedDependsPhasePath -Force
    }

    [System.IO.File]::WriteAllBytes($mixedDependsRoadmapPath, $originalMixedDependsRoadmapBytes)
  }
}
Invoke-Step "Resolve semicolon Depends On header targets" {
  $tempSemicolonDependsPhasePath = Join-Path (Join-Path $PSScriptRoot "..") "PHASE_99_93_TEMP_SEMICOLON_DEPENDS_ON_HEADER.md"
  $semicolonDependsRoadmapPath = Join-Path (Join-Path $PSScriptRoot "..") "ROADMAP_CURRENT.json"
  $semicolonDependsUpdatePath = Join-Path $PSScriptRoot "update-roadmap.ps1"
  $expectedDependsOn = @(
    "PHASE_42_04_ROADMAP_METADATA_REGRESSION_GUARD.md"
    "PHASE_42_05_ROADMAP_REGRESSION_TESTING.md"
  )
  $originalSemicolonDependsRoadmapBytes = [System.IO.File]::ReadAllBytes($semicolonDependsRoadmapPath)

  try {
    @(
      "# PHASE 99.93 TEMP SEMICOLON DEPENDS ON HEADER"
      ""
      "Status: Proposed"
      "Documentation Only: Yes"
      "Owner: Operations / Governance"
      "Priority: High"
      "Depends On: Phase 42.04; PHASE_42_05_ROADMAP_REGRESSION_TESTING.md"
      ""
      "## Summary"
      "Temporary regression fixture for semicolon Depends On header target resolution."
    ) | Set-Content -Path $tempSemicolonDependsPhasePath -Encoding utf8

    & $semicolonDependsUpdatePath | Out-Null

    $roadmap = Get-Content -Raw -Path $semicolonDependsRoadmapPath | ConvertFrom-Json
    $phase = $roadmap.phases | Where-Object { $_.file -eq "PHASE_99_93_TEMP_SEMICOLON_DEPENDS_ON_HEADER.md" }

    if (-not $phase) {
      throw "Temporary semicolon Depends On phase was not generated into ROADMAP_CURRENT.json."
    }

    $actualDependsOn = @($phase.depends_on)

    if ($actualDependsOn.Count -ne $expectedDependsOn.Count) {
      throw "Semicolon Depends On header produced $($actualDependsOn.Count) dependencies, expected $($expectedDependsOn.Count). Actual: $($actualDependsOn -join ', ')"
    }

    for ($i = 0; $i -lt $expectedDependsOn.Count; $i++) {
      if ($actualDependsOn[$i] -ne $expectedDependsOn[$i]) {
        throw "Semicolon Depends On header dependency mismatch at index $i. Expected: $($expectedDependsOn[$i]). Actual: $($actualDependsOn[$i])"
      }
    }
  }
  finally {
    if (Test-Path $tempSemicolonDependsPhasePath) {
      Remove-Item $tempSemicolonDependsPhasePath -Force
    }

    [System.IO.File]::WriteAllBytes($semicolonDependsRoadmapPath, $originalSemicolonDependsRoadmapBytes)
  }
}
Invoke-Step "Reject missing Depends On header target" {
  $tempDependsPhasePath = Join-Path (Join-Path $PSScriptRoot "..") "PHASE_99_99_TEMP_MISSING_DEPENDS_ON_HEADER_TARGET.md"
  $dependsRoadmapPath = Join-Path (Join-Path $PSScriptRoot "..") "ROADMAP_CURRENT.json"
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
$roadmapPath = Join-Path (Join-Path $PSScriptRoot "..") "ROADMAP_CURRENT.json"
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

    & $validatorPath *> $null

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

Invoke-Step "Trim roadmap Status header value" {
  $tempTrimStatusPhasePath = Join-Path (Join-Path $PSScriptRoot "..") "PHASE_99_92_TEMP_TRIMMED_STATUS_HEADER.md"
  $trimStatusRoadmapPath = Join-Path (Join-Path $PSScriptRoot "..") "ROADMAP_CURRENT.json"
  $trimStatusUpdatePath = Join-Path $PSScriptRoot "update-roadmap.ps1"
  $originalTrimStatusRoadmapBytes = [System.IO.File]::ReadAllBytes($trimStatusRoadmapPath)

  try {
    @(
      "# PHASE 99.92 TEMP TRIMMED STATUS HEADER"
      ""
      "Status:   Proposed   "
      "Documentation Only: Yes"
      "Owner: Operations / Governance"
      "Priority: High"
      ""
      "## Summary"
      "Temporary regression fixture for trimmed Status header normalization."
    ) | Set-Content -Path $tempTrimStatusPhasePath -Encoding utf8

    & $trimStatusUpdatePath | Out-Null

    $roadmap = Get-Content -Raw -Path $trimStatusRoadmapPath | ConvertFrom-Json
    $phase = $roadmap.phases | Where-Object { $_.file -eq "PHASE_99_92_TEMP_TRIMMED_STATUS_HEADER.md" }

    if (-not $phase) {
      throw "Temporary trimmed Status phase was not generated into ROADMAP_CURRENT.json."
    }

    if ($phase.status -ne "recorded") {
      throw "Trimmed Status header produced unexpected status. Expected: recorded. Actual: $($phase.status)"
    }
  }
  finally {
    if (Test-Path $tempTrimStatusPhasePath) {
      Remove-Item $tempTrimStatusPhasePath -Force
    }

    [System.IO.File]::WriteAllBytes($trimStatusRoadmapPath, $originalTrimStatusRoadmapBytes)
  }
}

Invoke-Step "Trim roadmap Priority header value" {
  $tempTrimPriorityPhasePath = Join-Path (Join-Path $PSScriptRoot "..") "PHASE_99_91_TEMP_TRIMMED_PRIORITY_HEADER.md"
  $trimPriorityRoadmapPath = Join-Path (Join-Path $PSScriptRoot "..") "ROADMAP_CURRENT.json"
  $trimPriorityUpdatePath = Join-Path $PSScriptRoot "update-roadmap.ps1"
  $originalTrimPriorityRoadmapBytes = [System.IO.File]::ReadAllBytes($trimPriorityRoadmapPath)

  try {
    @(
      "# PHASE 99.91 TEMP TRIMMED Priority HEADER"
      ""
      "Priority:   High   "
      "Documentation Only: Yes"
      "Owner: Operations / Governance"
      ""
      "## Summary"
      "Temporary regression fixture for trimmed Priority header normalization."
    ) | Set-Content -Path $tempTrimPriorityPhasePath -Encoding utf8

    & $trimPriorityUpdatePath | Out-Null

    $roadmap = Get-Content -Raw -Path $trimPriorityRoadmapPath | ConvertFrom-Json
    $phase = $roadmap.phases | Where-Object { $_.file -eq "PHASE_99_91_TEMP_TRIMMED_PRIORITY_HEADER.md" }

    if (-not $phase) {
      throw "Temporary trimmed Priority phase was not generated into ROADMAP_CURRENT.json."
    }

    if ($phase.Priority -ne "high") {
      throw "Trimmed Priority header produced unexpected Priority. Expected: high. Actual: $($phase.Priority)"
    }
  }
  finally {
    if (Test-Path $tempTrimPriorityPhasePath) {
      Remove-Item $tempTrimPriorityPhasePath -Force
    }

    [System.IO.File]::WriteAllBytes($trimPriorityRoadmapPath, $originalTrimPriorityRoadmapBytes)
  }
}

Invoke-Step "Trim roadmap Owner header value" {
  $tempTrimOwnerPhasePath = Join-Path (Join-Path $PSScriptRoot "..") "PHASE_99_90_TEMP_TRIMMED_OWNER_HEADER.md"
  $trimOwnerRoadmapPath = Join-Path (Join-Path $PSScriptRoot "..") "ROADMAP_CURRENT.json"
  $trimOwnerUpdatePath = Join-Path $PSScriptRoot "update-roadmap.ps1"
  $originalTrimOwnerRoadmapBytes = [System.IO.File]::ReadAllBytes($trimOwnerRoadmapPath)

  try {
    @(
      "# PHASE 99.90 TEMP TRIMMED Owner HEADER"
      ""
      "Owner:   Operations / Governance   "
      "Priority: High"
      "Documentation Only: Yes"
      ""
      "## Summary"
      "Temporary regression fixture for trimmed Owner header normalization."
    ) | Set-Content -Path $tempTrimOwnerPhasePath -Encoding utf8

    & $trimOwnerUpdatePath | Out-Null

    $roadmap = Get-Content -Raw -Path $trimOwnerRoadmapPath | ConvertFrom-Json
    $phase = $roadmap.phases | Where-Object { $_.file -eq "PHASE_99_90_TEMP_TRIMMED_OWNER_HEADER.md" }

    if (-not $phase) {
      throw "Temporary trimmed Owner phase was not generated into ROADMAP_CURRENT.json."
    }

    if ($phase.Owner -ne "Operations / Governance") {
      throw "Trimmed Owner header produced unexpected Owner. Expected: Operations / Governance. Actual: $($phase.Owner)"
    }
  }
  finally {
    if (Test-Path $tempTrimOwnerPhasePath) {
      Remove-Item $tempTrimOwnerPhasePath -Force
    }

    [System.IO.File]::WriteAllBytes($trimOwnerRoadmapPath, $originalTrimOwnerRoadmapBytes)
  }
}

Invoke-Step "Trim roadmap Documentation Only header value" {
  $tempTrimDocumentationOnlyPhasePath = Join-Path (Join-Path $PSScriptRoot "..") "PHASE_99_89_TEMP_TRIMMED_DOCUMENTATION_ONLY_HEADER.md"
  $trimDocumentationOnlyRoadmapPath = Join-Path (Join-Path $PSScriptRoot "..") "ROADMAP_CURRENT.json"
  $trimDocumentationOnlyUpdatePath = Join-Path $PSScriptRoot "update-roadmap.ps1"
  $originalTrimDocumentationOnlyRoadmapBytes = [System.IO.File]::ReadAllBytes($trimDocumentationOnlyRoadmapPath)

  try {
    @(
      "# PHASE 99.89 TEMP TRIMMED DOCUMENTATION ONLY HEADER"
      ""
      "Owner: Operations / Governance"
      "Priority: High"
      "Documentation Only:   Yes   "
      ""
      "## Summary"
      "Temporary regression fixture for trimmed Documentation Only header normalization."
    ) | Set-Content -Path $tempTrimDocumentationOnlyPhasePath -Encoding utf8

    & $trimDocumentationOnlyUpdatePath | Out-Null

    $roadmap = Get-Content -Raw -Path $trimDocumentationOnlyRoadmapPath | ConvertFrom-Json
    $phase = $roadmap.phases | Where-Object { $_.file -eq "PHASE_99_89_TEMP_TRIMMED_DOCUMENTATION_ONLY_HEADER.md" }

    if (-not $phase) {
      throw "Temporary trimmed Documentation Only phase was not generated into ROADMAP_CURRENT.json."
    }

    $documentationOnlyProperty = $phase.PSObject.Properties["documentation_only"]

    if (-not $documentationOnlyProperty) {
      throw "Trimmed Documentation Only phase did not include expected JSON property: documentation_only"
    }

    if ([string]$documentationOnlyProperty.Value -ne "True") {
      throw "Trimmed Documentation Only header produced unexpected value. Expected: True. Actual: $($documentationOnlyProperty.Value)"
    }
  }
  finally {
    if (Test-Path $tempTrimDocumentationOnlyPhasePath) {
      Remove-Item $tempTrimDocumentationOnlyPhasePath -Force
    }

    [System.IO.File]::WriteAllBytes($trimDocumentationOnlyRoadmapPath, $originalTrimDocumentationOnlyRoadmapBytes)
  }
}

Invoke-Step "Treat Documentation Only Yes as true" {
  $tempDocumentationOnlyYesPhasePath = Join-Path (Join-Path $PSScriptRoot "..") "PHASE_99_88_TEMP_DOCUMENTATION_ONLY_YES.md"
  $documentationOnlyYesRoadmapPath = Join-Path (Join-Path $PSScriptRoot "..") "ROADMAP_CURRENT.json"
  $documentationOnlyYesUpdatePath = Join-Path $PSScriptRoot "update-roadmap.ps1"
  $originalDocumentationOnlyYesRoadmapBytes = [System.IO.File]::ReadAllBytes($documentationOnlyYesRoadmapPath)

  try {
    @(
      "# PHASE 99.88 TEMP DOCUMENTATION ONLY YES"
      ""
      "Owner: Operations / Governance"
      "Priority: High"
      "Documentation Only: Yes"
      ""
      "## Summary"
      "Temporary regression fixture for Documentation Only Yes semantics."
    ) | Set-Content -Path $tempDocumentationOnlyYesPhasePath -Encoding utf8

    & $documentationOnlyYesUpdatePath | Out-Null

    $roadmap = Get-Content -Raw -Path $documentationOnlyYesRoadmapPath | ConvertFrom-Json
    $phase = $roadmap.phases | Where-Object { $_.file -eq "PHASE_99_88_TEMP_DOCUMENTATION_ONLY_YES.md" }

    if (-not $phase) {
      throw "Temporary Documentation Only Yes phase was not generated into ROADMAP_CURRENT.json."
    }

    $documentationOnlyProperty = $phase.PSObject.Properties["documentation_only"]

    if (-not $documentationOnlyProperty) {
      throw "Documentation Only Yes phase did not include expected JSON property: documentation_only"
    }

    if ($documentationOnlyProperty.Value -ne $true) {
      throw "Documentation Only: Yes produced unexpected value. Expected: True. Actual: $($documentationOnlyProperty.Value)"
    }
  }
  finally {
    if (Test-Path $tempDocumentationOnlyYesPhasePath) {
      Remove-Item $tempDocumentationOnlyYesPhasePath -Force
    }

    [System.IO.File]::WriteAllBytes($documentationOnlyYesRoadmapPath, $originalDocumentationOnlyYesRoadmapBytes)
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

Invoke-Step "Treat Documentation Only No as false" {
  $tempDocumentationOnlyNoPhasePath = Join-Path (Join-Path $PSScriptRoot "..") "PHASE_99_87_TEMP_DOCUMENTATION_ONLY_NO.md"
  $documentationOnlyNoRoadmapPath = Join-Path (Join-Path $PSScriptRoot "..") "ROADMAP_CURRENT.json"
  $documentationOnlyNoUpdatePath = Join-Path $PSScriptRoot "update-roadmap.ps1"
  $originalDocumentationOnlyNoRoadmapBytes = [System.IO.File]::ReadAllBytes($documentationOnlyNoRoadmapPath)

  try {
    @(
      "# PHASE 99.87 TEMP DOCUMENTATION ONLY NO"
      ""
      "Owner: Operations / Governance"
      "Priority: High"
      "Documentation Only: No"
      ""
      "## Summary"
      "Temporary regression fixture for Documentation Only No semantics."
    ) | Set-Content -Path $tempDocumentationOnlyNoPhasePath -Encoding utf8

    & $documentationOnlyNoUpdatePath | Out-Null

    $roadmap = Get-Content -Raw -Path $documentationOnlyNoRoadmapPath | ConvertFrom-Json
    $phase = $roadmap.phases | Where-Object { $_.file -eq "PHASE_99_87_TEMP_DOCUMENTATION_ONLY_NO.md" }

    if (-not $phase) {
      throw "Temporary Documentation Only No phase was not generated into ROADMAP_CURRENT.json."
    }

    $documentationOnlyProperty = $phase.PSObject.Properties["documentation_only"]

    if (-not $documentationOnlyProperty) {
      throw "Temporary Documentation Only No phase did not include documentation_only."
    }

    if ($documentationOnlyProperty.Value -ne $false) {
      throw "Documentation Only: No produced unexpected value. Expected: False. Actual: $($documentationOnlyProperty.Value)"
    }
  }
  finally {
    if (Test-Path $tempDocumentationOnlyNoPhasePath) {
      Remove-Item -Path $tempDocumentationOnlyNoPhasePath -Force
    }

    [System.IO.File]::WriteAllBytes($documentationOnlyNoRoadmapPath, $originalDocumentationOnlyNoRoadmapBytes)
  }
}

Write-Host "Operational roadmap smoke test passed."



