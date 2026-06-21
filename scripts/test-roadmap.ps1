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

Write-Host "Operational roadmap smoke test passed."
