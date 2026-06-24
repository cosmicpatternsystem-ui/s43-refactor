param()

$ErrorActionPreference = "Stop"

$path = "ROADMAP_CURRENT.json"

function Fail {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Message
  )

  Write-Error $Message
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

if (!(Test-Path $path)) {
  Fail "ROADMAP_CURRENT.json is required but was not found."
}

try {
  $json = Get-Content $path -Raw | ConvertFrom-Json
} catch {
  Fail ("ROADMAP_CURRENT.json parse failed: " + $PSItem.Exception.Message)
}

$required = @(
  "schema_version",
  "source_of_truth",
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

if ($json.schema_version -lt 2) {
  Fail "ROADMAP_CURRENT.json schema_version must be 2 or greater."
}

if ($json.enforcement_model -ne "generated-and-diff-enforced-in-pr") {
  Fail "Invalid roadmap enforcement_model."
}

if ($json.generated_by -ne "scripts/update-roadmap.ps1") {
  Fail "Invalid roadmap generated_by value."
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

for ($i = 0; $i -lt $json.phases.Count; $i++) {
  $phase = $json.phases[$i]
  $scope = "phases[$i]"

  Assert-Property -Object $phase -Name "file" -Scope $scope
  Assert-Property -Object $phase -Name "status" -Scope $scope
  Assert-Property -Object $phase -Name "documentation_only" -Scope $scope
  Assert-Property -Object $phase -Name "owner" -Scope $scope
  Assert-Property -Object $phase -Name "priority" -Scope $scope
  Assert-ArrayProperty -Object $phase -Name "depends_on" -Scope $scope
  Assert-ArrayProperty -Object $phase -Name "acceptance_criteria" -Scope $scope
  Assert-ArrayProperty -Object $phase -Name "evidence" -Scope $scope
  Assert-Property -Object $phase -Name "last_verified_at" -Scope $scope

  if ([string]::IsNullOrWhiteSpace($phase.file)) {
    Fail "$scope file must not be empty."
  }

  if ($allowedStatuses -notcontains $phase.status) {
    Fail "$scope has invalid status: $($phase.status)"
  }

  if (($null -ne $phase.priority) -and ($allowedPriorities -notcontains $phase.priority)) {
    Fail "$scope has invalid priority: $($phase.priority)"
  }

  if (($null -ne $phase.last_verified_at) -and ($phase.last_verified_at -notmatch "^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")) {
    Fail "$scope last_verified_at must be an ISO-8601 UTC timestamp ending with Z."
  }
}

# Validate dependency references after all phase files are known.
$phaseFileSet = @{}

foreach ($phase in @($json.phases)) {
    $phaseFile = [string]$phase.file

    if ([string]::IsNullOrWhiteSpace($phaseFile)) {
        throw "Roadmap phase has an empty file value."
    }

    if ($phaseFileSet.ContainsKey($phaseFile)) {
        throw "Duplicate roadmap phase file: $phaseFile"
    }

    $phaseFileSet[$phaseFile] = $true
}

foreach ($phase in @($json.phases)) {
    $phaseFile = [string]$phase.file

    foreach ($dependency in @($phase.depends_on)) {
        $dependencyFile = [string]$dependency

        if ([string]::IsNullOrWhiteSpace($dependencyFile)) {
            throw "Roadmap phase '$phaseFile' has an empty depends_on entry."
        }

        if ($dependencyFile -eq $phaseFile) {
            throw "Roadmap phase '$phaseFile' cannot depend on itself."
        }

        if (-not $phaseFileSet.ContainsKey($dependencyFile)) {
            throw "Roadmap phase '$phaseFile' depends on missing phase '$dependencyFile'."
        }
    }
}
Write-Host "ROADMAP_CURRENT.json schema validation passed"


