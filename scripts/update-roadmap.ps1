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

    $metadata = $match.Groups[1].Value | ConvertFrom-Json

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

$phaseFiles = Get-ChildItem -Path . -Filter "PHASE_*.md" -File | Sort-Object Name

$phases = foreach ($phaseFile in $phaseFiles) {
    $content = Get-Content -Raw -Path $phaseFile.FullName
    $status = "recorded"

    if ($content -match "\bCOMPLETE\b") {
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


