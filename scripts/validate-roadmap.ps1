param(
  [string]$Path = (Join-Path (Join-Path $PSScriptRoot "..") "docs/governance/ROADMAP_CURRENT.json")
)

$ErrorActionPreference = "Stop"

function Fail {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Message
  )

  [Console]::Error.WriteLine($Message)
  exit 1
}

function Has-Property {
  param(
    [Parameter(Mandatory = $true)]
    [object]$Object,

    [Parameter(Mandatory = $true)]
    [string]$Name
  )

  return $Object.PSObject.Properties.Name.Contains($Name)
}

function Assert-Property {
  param(
    [Parameter(Mandatory = $true)]
    [object]$Object,

    [Parameter(Mandatory = $true)]
    [string]$Name,

    [Parameter(Mandatory = $true)]
    [string]$Scope
  )

  if (-not (Has-Property -Object $Object -Name $Name)) {
    Fail "$Scope missing required field: $Name"
  }
}

function Assert-ArrayProperty {
  param(
    [Parameter(Mandatory = $true)]
    [object]$Object,

    [Parameter(Mandatory = $true)]
    [string]$Name,

    [Parameter(Mandatory = $true)]
    [string]$Scope
  )

  Assert-Property -Object $Object -Name $Name -Scope $Scope

  $value = $Object.PSObject.Properties[$Name].Value
  if ($null -eq $value) {
    Fail "$Scope field must be an array: $Name"
  }

  if ($value -isnot [System.Array]) {
    Fail "$Scope field must be an array: $Name"
  }
}

if (!(Test-Path $Path)) {
  Fail "ROADMAP_CURRENT.json is required but was not found: $Path"
}

try {
  $json = Get-Content $Path -Raw | ConvertFrom-Json -DateKind String
} catch {
  Fail ("ROADMAP_CURRENT.json parse failed: " + $PSItem.Exception.Message)
}

$required = @(
  "schema_version",
  "roadmap_version",
  "authority",
  "lifecycle",
  "generated_by",
  "enforcement_model",
  "updated_at_utc",
  "phase_count",
  "operational_metadata_schema",
  "phases"
)

foreach ($field in $required) {
  Assert-Property -Object $json -Name $field -Scope "ROADMAP_CURRENT.json"
}

if ([string]$json.schema_version -ne "2.0") {
  Fail "ROADMAP_CURRENT.json schema_version must be `"2.0`"."
}

if ([string]$json.roadmap_version -ne "current") {
  Fail "ROADMAP_CURRENT.json roadmap_version must be `"current`"."
}

Assert-Property -Object $json.authority -Name "source" -Scope "authority"
if ([string]$json.authority.source -ne "repository_files_only") {
  Fail "authority.source must be `"repository_files_only`"."
}

Assert-Property -Object $json.lifecycle -Name "status" -Scope "lifecycle"
Assert-Property -Object $json.lifecycle -Name "updated_at" -Scope "lifecycle"

if ([string]::IsNullOrWhiteSpace([string]$json.lifecycle.status)) {
  Fail "lifecycle.status must not be empty."
}

if (($json.lifecycle.updated_at -notmatch "^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")) {
  Fail "lifecycle.updated_at must be an ISO-8601 UTC timestamp ending with Z."
}

if ($json.enforcement_model -ne "generated-and-diff-enforced-in-pr") {
  Fail "Invalid roadmap enforcement_model."
}

if ($json.generated_by -ne "scripts/update-roadmap.ps1") {
  Fail "Invalid roadmap generated_by value."
}

if (($json.updated_at_utc -notmatch "^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")) {
  Fail "updated_at_utc must be an ISO-8601 UTC timestamp ending with Z."
}

if ($json.phase_count -ne $json.phases.Count) {
  Fail "phase_count does not match phases.Count."
}

$metadataFields = @(
  "owner",
  "priority",
  "depends_on",
  "acceptance_criteria",
  "evidence",
  "last_verified_at"
)

foreach ($field in $metadataFields) {
  Assert-Property -Object $json.operational_metadata_schema -Name $field -Scope "operational_metadata_schema"
}

$allowedStatuses = @("recorded", "complete")
$allowedPriorities = @("critical", "high", "medium", "low")
$idPattern = '^P\d+[A-Z0-9-]*-[A-Z0-9-]+$'

for ($i = 0; $i -lt $json.phases.Count; $i++) {
  $phase = $json.phases[$i]
  $scope = "phases[$i]"

  Assert-Property -Object $phase -Name "id" -Scope $scope
  Assert-Property -Object $phase -Name "legacy_id" -Scope $scope
  Assert-Property -Object $phase -Name "file" -Scope $scope
  Assert-Property -Object $phase -Name "status" -Scope $scope
  Assert-Property -Object $phase -Name "documentation_only" -Scope $scope
  Assert-Property -Object $phase -Name "owner" -Scope $scope
  Assert-Property -Object $phase -Name "priority" -Scope $scope
  Assert-ArrayProperty -Object $phase -Name "depends_on" -Scope $scope
  Assert-ArrayProperty -Object $phase -Name "acceptance_criteria" -Scope $scope
  Assert-ArrayProperty -Object $phase -Name "evidence" -Scope $scope
  Assert-Property -Object $phase -Name "last_verified_at" -Scope $scope

  if ([string]::IsNullOrWhiteSpace([string]$phase.id)) {
    Fail "$scope id must not be empty."
  }

  if ([string]::IsNullOrWhiteSpace([string]$phase.legacy_id)) {
    Fail "$scope legacy_id must not be empty."
  }

  if ([string]::IsNullOrWhiteSpace([string]$phase.file)) {
    Fail "$scope file must not be empty."
  }

  if (($phase.id -notmatch $idPattern)) {
    Fail "$scope has invalid id format: $($phase.id)"
  }

  if ($allowedStatuses -notcontains $phase.status) {
    Fail "$scope has invalid status: $($phase.status)"
  }

  if (($null -ne $phase.priority) -and ($allowedPriorities -notcontains ([string]$phase.priority).ToLowerInvariant())) {
    Fail "$scope has invalid priority: $($phase.priority)"
  }

  $lastVerifiedAt = $phase.last_verified_at
  if ($lastVerifiedAt -is [datetime]) {
    $lastVerifiedAt = $lastVerifiedAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  }

  if (($null -ne $lastVerifiedAt) -and ($lastVerifiedAt -notmatch "^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")) {
    Fail "$scope last_verified_at must be an ISO-8601 UTC timestamp ending with Z."
  }
}

$phaseFileSet = @{}
$phaseIdSet = @{}

foreach ($phase in @($json.phases)) {
  $phaseFile = [string]$phase.file
  $phaseId = [string]$phase.id

  if ($phaseFileSet.ContainsKey($phaseFile)) {
    Fail "Duplicate roadmap phase file: $phaseFile"
  }

  if ($phaseIdSet.ContainsKey($phaseId)) {
    Fail "Duplicate roadmap phase id: $phaseId"
  }

  $phaseFileSet[$phaseFile] = $true
  $phaseIdSet[$phaseId] = $true
}

foreach ($phase in @($json.phases)) {
  $phaseFile = [string]$phase.file

  foreach ($dependency in @($phase.depends_on)) {
    $dependencyFile = [string]$dependency

    if ([string]::IsNullOrWhiteSpace($dependencyFile)) {
      Fail "Roadmap phase '$phaseFile' has an empty depends_on entry."
    }

    if ($dependencyFile -eq $phaseFile) {
      Fail "Roadmap phase '$phaseFile' cannot depend on itself."
    }

    if (-not $phaseFileSet.ContainsKey($dependencyFile)) {
      Fail "Roadmap phase '$phaseFile' depends on missing phase '$dependencyFile'."
    }
  }
}

Write-Host "ROADMAP_CURRENT.json schema validation passed"