param()

$ErrorActionPreference = "Stop"

$path = "ROADMAP_CURRENT.json"

if (!(Test-Path $path)) {
  Write-Error "ROADMAP_CURRENT.json is required but was not found."
  exit 1
}

try {
  $json = Get-Content $path -Raw | ConvertFrom-Json
} catch {
  Write-Error "ROADMAP_CURRENT.json is not valid JSON."
  exit 1
}

$required = @(
  "schema_version",
  "source_of_truth",
  "generated_by",
  "enforcement_model",
  "updated_at_utc",
  "phase_count",
  "phases"
)

foreach ($field in $required) {
  if (-not $json.PSObject.Properties.Name.Contains($field)) {
    Write-Error "ROADMAP_CURRENT.json missing required field: $field"
    exit 1
  }
}

if ($json.enforcement_model -ne "generated-and-diff-enforced-in-pr") {
  Write-Error "Invalid roadmap enforcement_model."
  exit 1
}

if ($json.generated_by -ne "scripts/update-roadmap.ps1") {
  Write-Error "Invalid roadmap generated_by value."
  exit 1
}

if ($json.phase_count -ne $json.phases.Count) {
  Write-Error "phase_count does not match phases.Count."
  exit 1
}

Write-Host "ROADMAP_CURRENT.json schema validation passed"
