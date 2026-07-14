#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    $current = (Get-Location).Path

    while ($true) {
        if (
            (Test-Path (Join-Path $current ".git")) -or
            (Test-Path (Join-Path $current "ROADMAP_CURRENT.json")) -or
            (Test-Path (Join-Path $current "ROADMAP_CANONICAL.md"))
        ) {
            return $current
        }

        $parent = Split-Path -Parent $current
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $current) {
            throw "Could not resolve repository root from current directory."
        }

        $current = $parent
    }
}

function Normalize-Newlines {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string] $Text
    )

    return (($Text -replace "`r`n", "`n") -replace "`r", "`n")
}

function Read-Utf8Text {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path
    )

    return [System.IO.File]::ReadAllText($Path, [System.Text.UTF8Encoding]::new($false))
}

function Write-Utf8Atomic {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string] $Content
    )

    $Content = Normalize-Newlines $Content

    $directory = Split-Path -Parent $Path
    if (-not (Test-Path $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }

    $tmp = Join-Path $directory (".{0}.{1}.tmp" -f ([IO.Path]::GetFileName($Path)), ([guid]::NewGuid().ToString("N")))

    try {
        [System.IO.File]::WriteAllText($tmp, $Content, [System.Text.UTF8Encoding]::new($false))

        if (Test-Path $Path) {
            Remove-Item -LiteralPath $Path -Force
        }

        Move-Item -LiteralPath $tmp -Destination $Path -Force
    }
    finally {
        if (Test-Path $tmp) {
            Remove-Item -LiteralPath $tmp -Force
        }
    }
}

function Backup-File {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $true)]
        [string] $Stamp
    )

    if (Test-Path $Path) {
        $backup = "$Path.authorityfix.$Stamp.bak"
        Copy-Item -LiteralPath $Path -Destination $backup -Force
        Write-Host "backup: $backup"
    }
}

function Get-FileSha256 {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path
    )

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Remove-ForbiddenAuthorityClaimsFromText {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string] $Text
    )

    $text = Normalize-Newlines $Text

    $text = $text -replace '(?im)^\s*<!--\s*ASOX:CANONICAL_HUMAN_METADATA\s*BEGIN\s*-->.*?^\s*<!--\s*ASOX:CANONICAL_HUMAN_METADATA\s*END\s*-->\s*\n?', ''
    $text = $text -replace '(?im)^\s*canonical_(human|machine)\s*[:=].*$\n?', ''
    $text = $text -replace '(?im)^\s*prevailing_authority\s*[:=].*$\n?', ''
    $text = $text -replace '(?im)^\s*independent_authority\s*[:=].*$\n?', ''
    $text = $text -replace '(?im)^\s*authority\s*[:=]\s*(canonical|prevailing|authoritative).*$\n?', ''
    $text = $text -replace '(?im)^\s*source_of_truth\s*[:=].*$\n?', ''
    $text = $text -replace '(?im)^\s*single_source_of_truth\s*[:=].*$\n?', ''

    return $text
}

function Ensure-DerivedMarkdownHeader {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $true)]
        [string] $Stamp
    )

    if (-not (Test-Path $Path)) {
        return
    }

    Backup-File -Path $Path -Stamp $Stamp

    $text = Read-Utf8Text $Path
    $text = Remove-ForbiddenAuthorityClaimsFromText $text
    $text = Normalize-Newlines $text

    $header = @'
<!--
DERIVED VIEW - NOT AUTHORITATIVE

This file is a non-prevailing derived view.
Canonical machine authority: ROADMAP_CURRENT.json
Canonical human authority: ROADMAP_CANONICAL.md
-->
'@

    $header = Normalize-Newlines $header

    if ($text -notmatch '(?is)DERIVED VIEW\s*-\s*NOT AUTHORITATIVE') {
        $text = $header.TrimEnd() + "`n`n" + $text.TrimStart()
    }
    else {
        $text = $text -replace '(?is)<!--\s*DERIVED VIEW\s*-\s*NOT AUTHORITATIVE.*?-->', $header.TrimEnd()
    }

    Write-Utf8Atomic -Path $Path -Content (($text.TrimEnd()) + "`n")
    Write-Host "fixed derived markdown: $Path"
}

function Ensure-CanonicalMarkdownMetadata {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $true)]
        [string] $MachinePath,

        [Parameter(Mandatory = $true)]
        [string] $Stamp
    )

    if (-not (Test-Path $Path)) {
        throw "Missing canonical human roadmap: $Path"
    }

    if (-not (Test-Path $MachinePath)) {
        throw "Missing canonical machine roadmap: $MachinePath"
    }

    Backup-File -Path $Path -Stamp $Stamp

    $sha = Get-FileSha256 -Path $MachinePath
    $text = Read-Utf8Text $Path
    $text = Normalize-Newlines $text

    $metadataTemplate = @'
<!-- ASOX:CANONICAL_HUMAN_METADATA BEGIN
canonical_human: ROADMAP_CANONICAL.md
canonical_machine: ROADMAP_CURRENT.json
canonical_machine_sha256: __SHA_PLACEHOLDER__
authority: canonical_human
independent_authority: true
state_files:
  - ROADMAP/ROADMAP_STATE.json: SUBORDINATE_DERIVED
derived_views:
  - ROADMAP.md
  - docs/ROADMAP.md
  - docs/roadmap/aso-x-integrated-mandatory-roadmap.md
  - docs/roadmap/roadmap.index.json
legacy_non_authoritative:
  - repo/roadmap/roadmap.yaml
ASOX:CANONICAL_HUMAN_METADATA END -->
'@

    $metadata = (Normalize-Newlines $metadataTemplate).Replace("__SHA_PLACEHOLDER__", $sha)

    $pattern = '(?im)^\s*<!--\s*ASOX:CANONICAL_HUMAN_METADATA\s*BEGIN\s*-->.*?^\s*<!--\s*ASOX:CANONICAL_HUMAN_METADATA\s*END\s*-->\s*'
    if ($text -match $pattern) {
        $text = [regex]::Replace($text, $pattern, $metadata.TrimEnd() + "`n`n", [System.Text.RegularExpressions.RegexOptions]::Singleline -bor [System.Text.RegularExpressions.RegexOptions]::Multiline)
    }
    else {
        $text = $metadata.TrimEnd() + "`n`n" + $text.TrimStart()
    }

    Write-Utf8Atomic -Path $Path -Content (($text.TrimEnd()) + "`n")
    Write-Host "fixed canonical metadata: $Path"
}

function Ensure-RoadmapStateJson {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $true)]
        [string] $Stamp
    )

    if (-not (Test-Path $Path)) {
        return
    }

    Backup-File -Path $Path -Stamp $Stamp

    $raw = Read-Utf8Text $Path
    $obj = $raw | ConvertFrom-Json

    foreach ($forbidden in @(
        "canonical_machine",
        "canonical_human",
        "non_canonical_machine",
        "non_canonical_human",
        "canonical_source",
        "non_canonical_source",
        "source_of_truth",
        "single_source_of_truth",
        "authoritative_source"
    )) {
        if ($obj.PSObject.Properties[$forbidden]) {
            $obj.PSObject.Properties.Remove($forbidden)
        }
    }

    $obj | Add-Member -NotePropertyName "authority" -NotePropertyValue "SUBORDINATE_DERIVED" -Force
    $obj | Add-Member -NotePropertyName "independent_authority" -NotePropertyValue $false -Force
    $obj | Add-Member -NotePropertyName "derived_machine_reference" -NotePropertyValue "ROADMAP_CURRENT.json" -Force
    $obj | Add-Member -NotePropertyName "derived_human_reference" -NotePropertyValue "ROADMAP.md" -Force
    $obj | Add-Member -NotePropertyName "role" -NotePropertyValue "subordinate_derived_state" -Force

    $json = $obj | ConvertTo-Json -Depth 100
    $json = Normalize-Newlines $json

    Write-Utf8Atomic -Path $Path -Content (($json.TrimEnd()) + "`n")
    Write-Host "fixed roadmap state json: $Path"
}


function Ensure-RoadmapIndexJson {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $false)]
        [string] $Stamp
    )

    if (-not (Test-Path $Path)) {
        return
    }

    if (-not [string]::IsNullOrEmpty($Stamp)) {
        Backup-File -Path $Path -Stamp $Stamp
    }

    $json = Read-Utf8Text $Path | ConvertFrom-Json -Depth 100

    # حذف کلیدهای ممنوعه حاکمیتی بدون حذف canonical_source
    foreach ($forbidden in @(
        "canonical_machine",
        "canonical_human",
        "non_canonical_source",
        "non_canonical_machine",
        "non_canonical_human",
        "canonical_roadmap",
        "canonical_index",
        "machine_readable_canonical_roadmap_index",
        "source_of_truth",
        "single_source_of_truth",
        "authoritative_source"
    )) {
        if ($json.PSObject.Properties[$forbidden]) {
            $json.PSObject.Properties.Remove($forbidden)
        }
    }

    # اعمال مقادیر منطبق بر پیاده‌سازی و تست‌های رسمی پروژه
    $json | Add-Member -NotePropertyName "canonical_source" -NotePropertyValue "ROADMAP_CANONICAL.md" -Force
    $json | Add-Member -NotePropertyName "derived_source_reference" -NotePropertyValue "ROADMAP_CANONICAL.md" -Force
    $json | Add-Member -NotePropertyName "derived_machine_reference" -NotePropertyValue "ROADMAP_MACHINE.json" -Force
    $json | Add-Member -NotePropertyName "derived_human_reference" -NotePropertyValue "ROADMAP_HUMAN.md" -Force
    $json | Add-Member -NotePropertyName "independent_authority" -NotePropertyValue $false -Force
    $json | Add-Member -NotePropertyName "machine_readable_state" -NotePropertyValue "ROADMAP_CURRENT.json" -Force
    $json | Add-Member -NotePropertyName "role" -NotePropertyValue "traceability_index" -Force
    $json | Add-Member -NotePropertyName "authority" -NotePropertyValue "non-prevailing" -Force
    $json | Add-Member -NotePropertyName "status" -NotePropertyValue "active" -Force
    $json | Add-Member -NotePropertyName "horizon_years" -NotePropertyValue 50 -Force

    $out = ($json | ConvertTo-Json -Depth 100)
    $out = (($out -replace "`r`n", "`n") -replace "`r", "`n").TrimEnd("`n") + "`n"
    Write-Utf8Atomic -Path $Path -Content $out
    Write-Host "fixed roadmap index json: $Path"
}


function Ensure-LegacyYamlNonAuthoritative {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $true)]
        [string] $Stamp
    )

    if (-not (Test-Path $Path)) {
        return
    }

    Backup-File -Path $Path -Stamp $Stamp

    $text = Read-Utf8Text $Path
    $text = Normalize-Newlines $text

    $text = $text -replace '(?im)^\s*authority\s*:.*$', 'authority: legacy_non_authoritative'
    $text = $text -replace '(?im)^\s*role\s*:.*$', 'role: legacy_non_authoritative'
    $text = $text -replace '(?im)^\s*independent_authority\s*:.*$', 'independent_authority: false'
    $text = $text -replace '(?im)^\s*canonical\s*:.*$', 'canonical: ROADMAP_CURRENT.json'
    $text = $text -replace '(?im)^\s*source_of_truth\s*:.*$', 'source_of_truth: ROADMAP_CURRENT.json'

    if ($text -notmatch '(?im)^\s*authority\s*:') {
        $text += "`nauthority: legacy_non_authoritative"
    }

    if ($text -notmatch '(?im)^\s*role\s*:') {
        $text += "`nrole: legacy_non_authoritative"
    }

    if ($text -notmatch '(?im)^\s*independent_authority\s*:') {
        $text += "`nindependent_authority: false"
    }

    if ($text -notmatch '(?im)^\s*canonical\s*:') {
        $text += "`ncanonical: ROADMAP_CURRENT.json"
    }

    Write-Utf8Atomic -Path $Path -Content (($text.TrimEnd()) + "`n")
    Write-Host "fixed legacy yaml: $Path"
}

function Invoke-RoadmapAuthorityGate {
    param(
        [Parameter(Mandatory = $true)]
        [string] $RepoRoot
    )

    Write-Host ""
    Write-Host "running gate..."

    $gate = Join-Path $RepoRoot "scripts\run-roadmap-authority-gate.ps1"
    if (Test-Path $gate) {
        & pwsh -NoProfile -ExecutionPolicy Bypass -File $gate
        return $LASTEXITCODE
    }

    $validator = Join-Path $RepoRoot "scripts\validate_roadmap_authority.py"
    if (Test-Path $validator) {
        & python $validator
        return $LASTEXITCODE
    }

    Write-Warning "No roadmap authority gate script found."
    return 0
}

$exitCode = 1

try {
    $repoRoot = Resolve-RepoRoot
    Set-Location $repoRoot

    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"

    Write-Host "repo root: $repoRoot"
    Write-Host "repair stamp: $stamp"
    Write-Host ""

    $canonicalMachine = Join-Path $repoRoot "ROADMAP_CURRENT.json"
    $canonicalHuman = Join-Path $repoRoot "ROADMAP_CANONICAL.md"

    Ensure-CanonicalMarkdownMetadata `
        -Path $canonicalHuman `
        -MachinePath $canonicalMachine `
        -Stamp $stamp

    Ensure-DerivedMarkdownHeader `
        -Path (Join-Path $repoRoot "ROADMAP.md") `
        -Stamp $stamp

    Ensure-DerivedMarkdownHeader `
        -Path (Join-Path $repoRoot "docs\ROADMAP.md") `
        -Stamp $stamp

    Ensure-DerivedMarkdownHeader `
        -Path (Join-Path $repoRoot "docs\roadmap\aso-x-integrated-mandatory-roadmap.md") `
        -Stamp $stamp

    Ensure-RoadmapIndexJson `
        -Path (Join-Path $repoRoot "docs\roadmap\roadmap.index.json") `
        -Stamp $stamp

    Ensure-RoadmapStateJson `
        -Path (Join-Path $repoRoot "ROADMAP\ROADMAP_STATE.json") `
        -Stamp $stamp

    Ensure-LegacyYamlNonAuthoritative `
        -Path (Join-Path $repoRoot "repo\roadmap\roadmap.yaml") `
        -Stamp $stamp

    $exitCode = Invoke-RoadmapAuthorityGate -RepoRoot $repoRoot

    Write-Host ""
    Write-Host "done. Backups were created with suffix: .authorityfix.$stamp.bak"
}
catch {
    Write-Error $_
    $exitCode = 1
}
finally {
    exit $exitCode
}
