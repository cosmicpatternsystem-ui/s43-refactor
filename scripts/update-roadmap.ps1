function ConvertTo-JsonStringLiteral {
    param([AllowNull()][string]$Text)
    if ($null -eq $Text) { return '""' }
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append('"')
    foreach ($ch in $Text.ToCharArray()) {
        $code = [int]$ch
        switch ($ch) {
            '"'  { [void]$sb.Append('\"') }
            '\'  { [void]$sb.Append('\\') }
            "`b" { [void]$sb.Append('\b') }
            "`f" { [void]$sb.Append('\f') }
            "`n" { [void]$sb.Append('\n') }
            "`r" { [void]$sb.Append('\r') }
            "`t" { [void]$sb.Append('\t') }
            default {
                if ($code -lt 0x20) { [void]$sb.Append('\u{0:x4}' -f $code) }
                else { [void]$sb.Append($ch) }
            }
        }
    }
    [void]$sb.Append('"')
    return $sb.ToString()
}

function Format-CanonicalJson {
    param($Value, [int]$Depth = 0)

    if ($Depth -gt 64) {
        throw "Format-CanonicalJson: max nesting depth (64) exceeded at depth $Depth (cyclic or self-referential value)."
    }

    $pad  = '  ' * $Depth
    $padN = '  ' * ($Depth + 1)

    if ($null -eq $Value)   { return 'null' }
    if ($Value -is [bool])  { if ($Value) { return 'true' } else { return 'false' } }
    if ($Value -is [string]){ return (ConvertTo-JsonStringLiteral $Value) }

    if ($Value -is [datetime]) {
        $iso = $Value.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ", [System.Globalization.CultureInfo]::InvariantCulture)
        return (ConvertTo-JsonStringLiteral $iso)
    }
    if ($Value -is [System.DateTimeOffset]) {
        $iso = $Value.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ", [System.Globalization.CultureInfo]::InvariantCulture)
        return (ConvertTo-JsonStringLiteral $iso)
    }

    if ($Value -is [int] -or $Value -is [long] -or $Value -is [double] -or
        $Value -is [decimal] -or $Value -is [single] -or $Value -is [byte] -or $Value -is [int16]) {
        return ([System.Convert]::ToString($Value, [System.Globalization.CultureInfo]::InvariantCulture))
    }

    if ($Value -is [System.Collections.IDictionary]) {
        $keys = @($Value.Keys)
        if ($keys.Count -eq 0) { return '{}' }
        $parts = foreach ($k in $keys) {
            '{0}{1}: {2}' -f $padN, (ConvertTo-JsonStringLiteral ([string]$k)), (Format-CanonicalJson $Value[$k] ($Depth + 1))
        }
        return "{`n" + ($parts -join ",`n") + "`n$pad}"
    }

    if ($Value -isnot [string] -and $Value -is [System.Collections.IEnumerable]) {
        $arr = @($Value)
        if ($arr.Count -eq 0) { return '[]' }
        $parts = foreach ($item in $arr) {
            '{0}{1}' -f $padN, (Format-CanonicalJson $item ($Depth + 1))
        }
        return "[`n" + ($parts -join ",`n") + "`n$pad]"
    }

    if ($Value -is [System.ValueType]) {
        return (ConvertTo-JsonStringLiteral ([string]$Value))
    }

    $props = @($Value.PSObject.Properties | Where-Object { $_.MemberType -in 'NoteProperty','Property' })
    if ($props.Count -eq 0) { return '{}' }
    $parts = foreach ($p in $props) {
        '{0}{1}: {2}' -f $padN, (ConvertTo-JsonStringLiteral $p.Name), (Format-CanonicalJson $p.Value ($Depth + 1))
    }
    return "{`n" + ($parts -join ",`n") + "`n$pad}"
}

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

function Normalize-RoadmapBoolean {
    param(
        [object]$Value
    )

    $normalized = Normalize-RoadmapScalar $Value

    if ($null -eq $normalized) {
        return $null
    }

    switch ($normalized.ToLowerInvariant()) {
        "true" { return $true }
        "yes" { return $true }
        "y" { return $true }
        "1" { return $true }
        "on" { return $true }

        "false" { return $false }
        "no" { return $false }
        "n" { return $false }
        "0" { return $false }
        "off" { return $false }

        default { return $null }
    }
}
function Get-MetadataValue {
    param(
        [string]$Content,
        [string]$Name
    )

    $pattern = "(?im)^[ \t]*" + [regex]::Escape($Name) + "[ \t]*:[ \t]*([^\r\n]*?)[ \t]*\r?$"
    $match = [regex]::Match($Content, $pattern)

    if ($match.Success) {
        return $match.Groups[1].Value.Trim()
    }

    return $null
}

function Normalize-RoadmapList {
    param(
        [object]$Value
    )

    if ($null -eq $Value) {
        return @()
    }

    $items = @()

    foreach ($item in @($Value)) {
        if ($null -eq $item) {
            continue
        }

        $parts = ([string]$item) -split "[,;]"

        foreach ($part in $parts) {
            $normalized = Normalize-RoadmapScalar $part

            if ($null -ne $normalized) {
                $items += $normalized
            }
        }
    }

    return @($items)
}

function Get-PhaseReferenceMap {
    param(
        [object[]]$PhaseFiles
    )

    $map = @{}

    foreach ($phaseFile in $PhaseFiles) {
        $key = [System.IO.Path]::GetFileNameWithoutExtension($phaseFile.Name)
        $map[$phaseFile.Name.ToLowerInvariant()] = $phaseFile.Name
        $map[$key.ToLowerInvariant()] = $phaseFile.Name

        if ($key -match '^PHASE_(\d+)_(\d+)_') {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            $minorPadded = '{0:D2}' -f $minor

            foreach ($label in @(
                "Phase $major.$minorPadded",
                "PHASE $major.$minorPadded",
                "$major.$minorPadded",
                "Phase $major.$minor",
                "PHASE $major.$minor",
                "$major.$minor"
            )) {
                $map[$label.ToLowerInvariant()] = $phaseFile.Name
            }
        }
    }

    return $map
}

function Resolve-RoadmapDependsOn {
    param(
        [object]$Value,
        [hashtable]$PhaseReferenceMap
    )

    $resolved = @()

    foreach ($item in @(Normalize-RoadmapList $Value)) {
        $normalized = Normalize-RoadmapScalar $item

        if ($null -eq $normalized) {
            continue
        }

        $lookupKey = $normalized.ToLowerInvariant()

        if ($PhaseReferenceMap.ContainsKey($lookupKey)) {
            $resolved += $PhaseReferenceMap[$lookupKey]
        }
        else {
            $resolved += $normalized
        }
    }

    return @($resolved)
}
$phaseFiles = Get-ChildItem -Path . -Filter "PHASE_*.md" -File | Sort-Object Name
$phaseReferenceMap = Get-PhaseReferenceMap -PhaseFiles $phaseFiles

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

        $documentationOnlyValue = $metadata["documentation_only"]

        if ($null -eq $documentationOnlyValue) {
            $documentationOnlyValue = Get-MetadataValue -Content $content -Name "Documentation Only"
        }

        $normalizedDocumentationOnly = Normalize-RoadmapBoolean $documentationOnlyValue

        if ($null -ne $normalizedDocumentationOnly) {
            $documentationOnly = $normalizedDocumentationOnly
        }

        $dependsOn = @(Normalize-RoadmapList $metadata["depends_on"])

        if ($dependsOn.Count -eq 0) {
            $dependsOn = @(Normalize-RoadmapList (Get-MetadataValue -Content $content -Name "Depends On"))
        }

        $metadata["owner"] = Normalize-RoadmapScalar $metadata["owner"]
        $metadata["priority"] = Normalize-RoadmapPriority $metadata["priority"]
        $metadata["depends_on"] = Resolve-RoadmapDependsOn -Value $dependsOn -PhaseReferenceMap $phaseReferenceMap

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
    source_of_truth = "repository_files_only"
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
$json = Format-CanonicalJson -Value $roadmap
$json = $json.Replace("`r`n", "`n") + "`n"

& (Join-Path $PSScriptRoot "Write-AtomicJson.ps1") -Path (Join-Path (Get-Location) "ROADMAP_CURRENT.json") -Data $json

Write-Host "ROADMAP_CURRENT.json regenerated from PHASE_*.md files"










