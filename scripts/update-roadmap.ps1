Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-RoadmapMetadata {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Content
    )

    $defaults = [ordered]@{
        owner = $null
        priority = $null
        depends_on = @()
        acceptance_criteria = @()
        evidence = @()
        last_verified_at = $null
    }

    $match = [regex]::Match(
        $Content,
        "(?s)<!--\s*roadmap-metadata\s*(\{.*?\})\s*-->"
    )

    if (-not $match.Success) {
        return $defaults
    }

    $metadata = $match.Groups[1].Value | ConvertFrom-Json -DateKind String

    foreach ($key in @("owner", "priority", "depends_on", "acceptance_criteria", "evidence", "last_verified_at")) {
        if ($metadata.PSObject.Properties.Name -contains $key) {
            $defaults[$key] = $metadata.$key
        }
    }

    foreach ($arrayKey in @("depends_on", "acceptance_criteria", "evidence")) {
        if ($null -eq $defaults[$arrayKey]) {
            $defaults[$arrayKey] = @()
        } else {
            $defaults[$arrayKey] = @($defaults[$arrayKey])
        }
    }

    return $defaults
}



function Normalize-RoadmapPriority {
    param(
        [object]$Value
    )

    if ($null -eq $Value) {
        return $null
    }

    $normalized = [string]$Value
    $normalized = $normalized.Trim()
    $normalized = $normalized.Trim('"')
    $normalized = $normalized.Trim("'")
    $normalized = $normalized.Trim().ToLowerInvariant()

    switch ($normalized) {
        "critical" { return "Critical" }
        "high" { return "High" }
        "medium" { return "Medium" }
        "low" { return "Low" }
        default { return $Value }
    }
}

function Normalize-RoadmapScalar {
    param(
        [object]$Value
    )

    if ($null -eq $Value) {
        return $null
    }

    $normalized = [string]$Value
    $normalized = $normalized.Trim()
    $normalized = $normalized.Trim('"')
    $normalized = $normalized.Trim("'")
    $normalized = $normalized.Trim()

    if ($normalized -eq "") {
        return $null
    }

    return $normalized
}

function Normalize-RoadmapPriority {
    param(
        [object]$Value
    )

    $normalized = Normalize-RoadmapScalar $Value

    if ($null -eq $normalized) {
        return $null
    }

    switch ($normalized.ToLowerInvariant()) {
        "critical" { return "Critical" }
        "high" { return "High" }
        "medium" { return "Medium" }
        "low" { return "Low" }
        default { return $normalized }
    }
}
function Get-MetadataValue {
    param(
        [string]$Content,
        [string]$Name
    )

    $pattern = "(?im)^\s*" + [regex]::Escape($Name) + "\s*:\s*(.+?)\s*$"
    $match = [regex]::Match($Content, $pattern)

    if ($match.Success) {
        return $match.Groups[1].Value.Trim()
    }

    return $null
}
$phaseFiles = Get-ChildItem -Path . -Filter "PHASE_*.md" -File | Sort-Object Name

$phases = foreach ($phaseFile in $phaseFiles) {
    $content = Get-Content -Raw -Path $phaseFile.FullName
    $statusValue = Get-MetadataValue -Content $content -Name "Status"
        $status = "recorded"

        if ($statusValue) {
            $normalizedStatus = $statusValue.Trim().ToLowerInvariant()

            if ($normalizedStatus -match "\brecorded\b") {
                $status = "recorded"
            }
            elseif (
                $normalizedStatus -match "\bcomplete\b" -or
                $normalizedStatus -match "\bcompleted\b"
            ) {
                $status = "complete"
            }
        }
        elseif ($content -match "\bCOMPLETE\b") {
            $status = "complete"
        }

    $documentationOnly = $false
    if (
        $content -match "(?i)documentation-only" -or
        $content -match "(?i)\bno-op\b" -or
        (
            $content -match "(?i)no code" -and
            $content -match "(?i)no runtime" -and
            $content -match "(?i)no deployment"
        )
    ) {
        $documentationOnly = $true
    }

    $metadata = Get-RoadmapMetadata -Content $content

        # Phase 42.03 header metadata backfill
        if (-not $metadata["owner"]) {
            $metadata["owner"] = Get-MetadataValue -Content $content -Name "Owner"
        }

        if (-not $metadata["priority"]) {
            $metadata["priority"] = Get-MetadataValue -Content $content -Name "Priority"
        }

        $metadata["owner"] = Normalize-RoadmapScalar $metadata["owner"]
        $metadata["priority"] = Normalize-RoadmapPriority $metadata["priority"]

    [ordered]@{
        file = $phaseFile.Name
        status = $status
        documentation_only = $documentationOnly
        owner = $metadata.owner
        priority = $metadata.priority
        depends_on = @($metadata.depends_on)
        acceptance_criteria = @($metadata.acceptance_criteria)
        evidence = @($metadata.evidence)
        last_verified_at = $metadata.last_verified_at
    }
}

$roadmap = [ordered]@{
    schema_version = 2
    source_of_truth = "repository phase documents"
    generated_by = "scripts/update-roadmap.ps1"
    enforcement_model = "generated-and-diff-enforced-in-pr"
    operational_metadata_schema = [ordered]@{
        owner = "string|null"
        priority = "critical|high|medium|low|null"
        depends_on = "string[]"
        acceptance_criteria = "string[]"
        evidence = "string[]"
        last_verified_at = "ISO-8601 UTC string|null"
    }
    updated_at_utc = "GENERATED"
    phase_count = @($phases).Count
    phases = @($phases)
}

$json = $roadmap | ConvertTo-Json -Depth 20
$json = $json.Replace("`r`n", "`n") + "`n"

[System.IO.File]::WriteAllText(
    (Join-Path (Get-Location) "ROADMAP_CURRENT.json"),
    $json,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "ROADMAP_CURRENT.json regenerated from PHASE_*.md files"





