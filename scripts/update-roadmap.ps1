function Get-CanonicalRoadmapEntries {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        throw "Canonical roadmap file not found: $Path"
    }

    $lines = Get-Content -Path $Path
    $entries = @()
    $seen = @{}

    foreach ($line in $lines) {
        $matches = [regex]::Matches($line, '\bP\d-[A-Z0-9-]+\b')
        foreach ($match in $matches) {
            $id = $match.Value
            if (-not $seen.ContainsKey($id)) {
                $seen[$id] = $true

                $title = $id
                $suffix = $line.Substring($match.Index + $match.Length).Trim()
                if (-not [string]::IsNullOrWhiteSpace($suffix)) {
                    $suffix = $suffix.TrimStart(':', '-').Trim()
                    if (-not [string]::IsNullOrWhiteSpace($suffix)) {
                        $title = $suffix
                    }
                }

                $entries += [pscustomobject]@{
                    id    = $id
                    title = $title
                }
            }
        }
    }

    return @($entries)
}

function Get-RoadmapPhaseId {
    param(
        [string]$FileName,
        [string]$Content
    )

    $sources = @($Content, $FileName)
    foreach ($source in $sources) {
        if ([string]::IsNullOrWhiteSpace($source)) { continue }
        $m = [regex]::Match($source, '\bP\d-[A-Z0-9-]+\b')
        if ($m.Success) { return $m.Value }
    }

    if ($FileName) {
        $base = [System.IO.Path]::GetFileNameWithoutExtension($FileName).ToUpperInvariant()
        $base = $base -replace '[^A-Z0-9]+', '-'
        $base = $base.Trim('-')
        return "P0-$base"
    }

    return "P0-UNSPECIFIED"
}
function Merge-CanonicalRoadmapPhases {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$GeneratedPhases,

        [Parameter(Mandatory = $true)]
        [object[]]$CanonicalEntries
    )

    $knownIds = @{}
    $merged = @()

    foreach ($phase in $GeneratedPhases) {
        $merged += $phase
        if ($null -ne $phase -and $phase.PSObject.Properties['id'] -and $phase.id) {
            $knownIds[[string]$phase.id] = $true
        }
    }

    foreach ($entry in $CanonicalEntries) {
        if (-not $knownIds.ContainsKey([string]$entry.id)) {
            if ([string]::IsNullOrWhiteSpace([string]$entry.id)) {
                $canonicalLegacyId = "docs/governance/ROADMAP_CANONICAL.md"
                $canonicalFile = "docs/governance/ROADMAP_CANONICAL.md"
            }
            else {
                $canonicalLegacyId = [string]$entry.id
                $canonicalFile = "docs/governance/ROADMAP_CANONICAL.md#" + ([string]$entry.id)
            }

            $merged += [ordered]@{
                id                  = $entry.id
                legacy_id           = $canonicalLegacyId
                title               = $entry.title
                file                = $canonicalFile
                status              = "recorded"
                documentation_only  = $true
                owner               = $null
                priority            = $null
                depends_on          = @()
                acceptance_criteria = @()
                evidence            = @()
                last_verified_at    = $null
            }
        }
    }

    return @($merged)
}

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

    if ($match.Success) {
        $metadata = $match.Groups[1].Value | ConvertFrom-Json

        foreach ($key in @("owner", "priority", "depends_on", "acceptance_criteria", "evidence", "last_verified_at")) {
            if ($metadata.PSObject.Properties.Name -contains $key) {
                $defaults[$key] = $metadata.$key
            }
        }
    }
    # Phase-42.03: parse YAML frontmatter (takes precedence over comment-based metadata)
    if ($content -match '(?ms)^---\s*\r?\n(.*?)\r?\n---') {
        $yamlText = $Matches[1]
        $yamlLines = $yamlText -split '\r?\n'
        $currentKey = $null
        $isArray = $false
        $arrayBuffer = @()

        foreach ($line in $yamlLines) {
            if ($line -match '^\s*$') { continue }

            if ($line -match '^(\w+):\s*"(.+)"$') {
                # scalar string: owner: "value"
                if ($currentKey -and $isArray) {
                    $defaults[$currentKey] = $arrayBuffer
                    $arrayBuffer = @()
                }
                $defaults[$Matches[1]] = $Matches[2]
                $currentKey = $null
                $isArray = $false
            }
            elseif ($line -match '^(\w+):\s*\[\s*\]\s*$') {
                # inline empty array: depends_on: []
                if ($currentKey -and $isArray) {
                    $defaults[$currentKey] = $arrayBuffer
                    $arrayBuffer = @()
                }
                $defaults[$Matches[1]] = @()
                $currentKey = $null
                $isArray = $false
            }
            elseif ($line -match '^(\w+):\s*(.+)$') {
                # scalar unquoted: priority: high, status: complete
                if ($currentKey -and $isArray) {
                    $defaults[$currentKey] = $arrayBuffer
                    $arrayBuffer = @()
                }
                $defaults[$Matches[1]] = $Matches[2]
                $currentKey = $null
                $isArray = $false
            }
            elseif ($line -match '^(\w+):\s*$') {
                # array start: acceptance_criteria:
                if ($currentKey -and $isArray) {
                    $defaults[$currentKey] = $arrayBuffer
                }
                $currentKey = $Matches[1]
                $isArray = $true
                $arrayBuffer = @()
            }
            elseif ($line -match '^\s+-\s+"(.+)"$') {
                # array item quoted
                if ($isArray) { $arrayBuffer += $Matches[1] }
            }
            elseif ($line -match '^\s+-\s+(.+)$') {
                # array item unquoted
                if ($isArray) { $arrayBuffer += $Matches[1] }
            }
        }
        # flush last array
        if ($currentKey -and $isArray) {
            $defaults[$currentKey] = $arrayBuffer
        }
    }


    # Convert string literals like '[]' to empty arrays
    foreach ($k in @("depends_on", "acceptance_criteria", "evidence")) {
        if ($metadata.PSObject.Properties.Name -contains $k) {
            $v = $metadata.$k
            if ($v -is [string] -and $v.Trim() -eq '[]') {
                $metadata.$k = @()
            }
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
$phaseFiles = Get-ChildItem -Path . -Recurse -Filter "PHASE_*.md" -File | Sort-Object Name
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
        # Phase-42.03: extract phase_id and title from H1 header
        $phaseId = $null
        $title   = $null
        $firstHeader = ($content -split "`n" |
            Where-Object { $_ -match '^#\s+Phase\s' } |
            Select-Object -First 1)

        if ($firstHeader -match '\b(P\d-[A-Z0-9-]+)\b') {
            $phaseId = $Matches[1]
            if (-not $title) {
                $title = $firstHeader -replace '^#\s+',''
                $title = $title -replace '.*\bP\d-[A-Z0-9-]+\b\s*[:\-]?\s*',''
                $title = $title.Trim()
            }
        } elseif ($content -match '\b(P\d-[A-Z0-9-]+)\b') {
            $phaseId = $Matches[1]
        }

        $legacyPhaseId = $null
        if ($firstHeader -match '^#\s+Phase\s+([\d]+)\.(\d+)\s+-\s+(.+?)\s*$') {
            $legacyPhaseId = "PHASE_$($Matches[1])_$('{0:D2}' -f [int]$Matches[2])"
            if (-not $title) { $title = $Matches[3].Trim() }
        } elseif ($firstHeader -match '^#\s+Phase\s+([\d]+)\s+-\s+(.+?)\s*$') {
            $legacyPhaseId = "PHASE_$($Matches[1])"
            if (-not $title) { $title = $Matches[2].Trim() }
        }

        if (-not $phaseId) {
            $fileStem = [System.IO.Path]::GetFileNameWithoutExtension($phaseFile.Name).ToUpperInvariant()
            $fileStem = $fileStem -replace '[^A-Z0-9]+', '-'
            $fileStem = $fileStem.Trim('-')
            $phaseId = "P0-$fileStem"
        }

        if (-not $legacyPhaseId) {
            $legacyPhaseId = [System.IO.Path]::GetFileNameWithoutExtension($phaseFile.Name)
        }

    $primaryRoadmapId = $phaseId
    if ([string]::IsNullOrWhiteSpace($legacyPhaseId)) {
        $legacyPhaseId = [System.IO.Path]::GetFileNameWithoutExtension($phaseFile.Name)
    }

    if ([string]::IsNullOrWhiteSpace($title)) {
        $title = [System.IO.Path]::GetFileNameWithoutExtension($phaseFile.Name)
    }

    [ordered]@{
        id = $primaryRoadmapId
        legacy_id = $legacyPhaseId
        title = $title
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


$canonicalRoadmapPath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\docs\governance\ROADMAP_CANONICAL.md"))
$canonicalEntries = Get-CanonicalRoadmapEntries -Path $canonicalRoadmapPath
$phases = Merge-CanonicalRoadmapPhases -GeneratedPhases @($phases) -CanonicalEntries @($canonicalEntries)
$roadmap = [ordered]@{
    schema_version = "2.0"
    roadmap_version = "current"
    source_of_truth = "repository_files_only"
    generated_by = "scripts/update-roadmap.ps1"
    enforcement_model = "generated-and-diff-enforced-in-pr"
    canonical_roadmap = "docs/governance/ROADMAP_CANONICAL.md"
    authority = [ordered]@{
        source = "repository_files_only"
        canonical_roadmap = "docs/governance/ROADMAP_CANONICAL.md"
        generated_by = "scripts/update-roadmap.ps1"
        enforcement_model = "generated-and-diff-enforced-in-pr"
    }
    lifecycle = [ordered]@{
        status = "active"
        updated_at = "GENERATED"
        updated_at_utc = "GENERATED"
    }
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
# === Stable Timestamp Logic ===
$outputPath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\docs\governance\ROADMAP_CURRENT.json"))
$existingTimestamp = $null; $existingJsonContent = $null
if (Test-Path $outputPath) {
    try {
        $existingJsonContent = Get-Content -Raw -Path $outputPath -ErrorAction Stop
        if ($existingJsonContent) {
            $existingData = $existingJsonContent | ConvertFrom-Json
            $existingTimestamp = $existingData.updated_at_utc; if (-not $existingTimestamp -and $existingData.lifecycle) { $existingTimestamp = $existingData.lifecycle.updated_at_utc }
        }
    } catch { Write-Verbose "Cannot parse existing roadmap: $_" }
}
function Get-StringHash { param([string]$Text)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $stream = [System.IO.MemoryStream]::new($bytes)
    try { (Get-FileHash -Algorithm SHA256 -InputStream $stream).Hash }
    finally { $stream.Dispose() } }
$roadmapForHash = [ordered]@{}
foreach ($k in $roadmap.Keys) { if ($k -ne "updated_at_utc") { $roadmapForHash[$k] = $roadmap[$k] } }
$jsonForHash = (Format-CanonicalJson -Value $roadmapForHash).Replace("`r`n", "`n")
$newHash = Get-StringHash $jsonForHash
$oldHash = $null
if ($existingJsonContent) {
    try {
        $ed = $existingJsonContent | ConvertFrom-Json
        $eo = [ordered]@{}
        foreach ($p in $ed.PSObject.Properties) {
            if ($p.Name -ne "updated_at_utc") { $eo[$p.Name] = $p.Value }
        }
        $oldHash = Get-StringHash (Format-CanonicalJson -Value $eo).Replace("`r`n", "`n")
    } catch { Write-Verbose "Hash existing failed: $_" }
}
if ($newHash -eq $oldHash -and $existingTimestamp) {
    $timestampToUse = $existingTimestamp
} else {
    $timestampToUse = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ", [System.Globalization.CultureInfo]::InvariantCulture)
}

$roadmap["updated_at_utc"] = $timestampToUse
if ($roadmap["lifecycle"]) {
    $roadmap["lifecycle"]["updated_at"] = $timestampToUse
    $roadmap["lifecycle"]["updated_at_utc"] = $timestampToUse
}

$json = Format-CanonicalJson -Value $roadmap
$json = $json.Replace("`r`n", "`n") + "`n"
& (Join-Path $PSScriptRoot "Write-AtomicJson.ps1") -Path $outputPath -Content $json

Write-Host "docs/governance/ROADMAP_CURRENT.json regenerated from PHASE_*.md files"
