#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($PSVersionTable.PSEdition -ne "Core") {
    throw "This repair must be run with PowerShell Core: pwsh -NoLogo -NoProfile -File .\scripts\repair-roadmap-authority.ps1"
}

$Root = (Resolve-Path ".").Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"

function Resolve-RepoPath {
    param([Parameter(Mandatory)][string]$Path)

    return [IO.Path]::GetFullPath((Join-Path $Root $Path))
}

function Backup-File {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    $backup = "$Path.authorityfix.$Stamp.bak"
    Copy-Item -LiteralPath $Path -Destination $backup -Force
    Write-Host "backup: $backup"
}

function Read-Utf8 {
    param([Parameter(Mandatory)][string]$Path)

    return [IO.File]::ReadAllText($Path, [Text.UTF8Encoding]::new($false))
}

function Write-Utf8Atomic {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Content
    )

    $full = [IO.Path]::GetFullPath($Path)
    $dir = [IO.Path]::GetDirectoryName($full)
    $tmp = Join-Path $dir ([IO.Path]::GetRandomFileName())

    [IO.File]::WriteAllText($tmp, $Content, [Text.UTF8Encoding]::new($false))

    try {
        Move-Item -LiteralPath $tmp -Destination $full -Force
    }
    finally {
        if (Test-Path -LiteralPath $tmp) {
            Remove-Item -LiteralPath $tmp -Force
        }
    }
}

function Normalize-Newlines {
    param([Parameter(Mandatory)][string]$Text)

    return ($Text -replace "`r`n", "`n" -replace "`r", "`n")
}

function Remove-ForbiddenAuthorityClaimsFromText {
    param([Parameter(Mandatory)][string]$Text)

    $t = Normalize-Newlines $Text

    $patterns = @(
        '(?im)^\s*Canonical source:\s*docs/ROADMAP\.md\s*$',
        '(?im)^\s*Canonical source:\s*ROADMAP\.md\s*$',
        '(?im)^\s*Machine-readable canonical roadmap index:\s*docs/roadmap/roadmap\.index\.json\s*$',
        '(?im)^\s*Machine-readable canonical roadmap index:\s*repo/roadmap/roadmap\.yaml\s*$',
        '(?im)^\s*Canonical machine-readable roadmap index:\s*docs/roadmap/roadmap\.index\.json\s*$',
        '(?im)^\s*Canonical machine-readable roadmap:\s*docs/roadmap/roadmap\.index\.json\s*$',
        '(?im)^\s*Canonical machine-readable roadmap:\s*repo/roadmap/roadmap\.yaml\s*$',
        '(?im)^\s*Source of truth:\s*docs/ROADMAP\.md\s*$',
        '(?im)^\s*Source of truth:\s*ROADMAP\.md\s*$',
        '(?im)^\s*Authority:\s*prevailing\s*$',
        '(?im)^\s*Authority:\s*authoritative\s*$'
    )

    foreach ($p in $patterns) {
        $t = [regex]::Replace($t, $p, "")
    }

    $t = [regex]::Replace($t, "`n{3,}", "`n`n")
    return $t.TrimStart()
}

function Ensure-DerivedMarkdownHeader {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Host "skip missing: $Path"
        return
    }

    Backup-File $Path
    $body = Read-Utf8 $Path
    $body = Remove-ForbiddenAuthorityClaimsFromText $body

    $header = @"
# DERIVED VIEW - NOT AUTHORITATIVE

Status: Active
Authority: non-prevailing
Canonical machine-readable roadmap state: `ROADMAP_CURRENT.json`
Canonical human-readable roadmap: `ROADMAP_CANONICAL.md`
Purpose: Derived/public/traceability view only. This file must not be used as the prevailing roadmap authority.

"@

    if ($body -notmatch '(?im)^\s*#\s*DERIVED VIEW\s*-\s*NOT AUTHORITATIVE\s*$') {
        $body = $header + ($body.TrimStart())
    }
    else {
        $body = Remove-ForbiddenAuthorityClaimsFromText $body
    }

    Write-Utf8Atomic -Path $Path -Content (($body.TrimEnd()) + "`n")
    Write-Host "fixed derived markdown: $Path"
}

function Ensure-CanonicalMarkdownMetadata {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing canonical roadmap: $Path"
    }

    Backup-File $Path
    $body = Read-Utf8 $Path
    $body = Normalize-Newlines $body

    $block = @"
# ASO-X Roadmap Canonical

Status: Active
Scope: ASO-X / s43-refactor
Authority: canonical-human
Canonical machine-readable roadmap state: `ROADMAP_CURRENT.json`
Canonical human-readable roadmap: `ROADMAP_CANONICAL.md`

"@

    $hasRequired =
        $body -match '(?im)^\s*Status:\s*Active\s*$' -and
        $body -match '(?im)^\s*Scope:\s*ASO-X\s*/\s*s43-refactor\s*$' -and
        $body -match '(?im)^\s*Canonical machine-readable roadmap state:\s*`?ROADMAP_CURRENT\.json`?\s*$' -and
        $body -match '(?im)^\s*Canonical human-readable roadmap:\s*`?ROADMAP_CANONICAL\.md`?\s*$'

    if (-not $hasRequired) {
        $body = $block + ($body.TrimStart())
    }

    Write-Utf8Atomic -Path $Path -Content (($body.TrimEnd()) + "`n")
    Write-Host "fixed canonical metadata: $Path"
}

function Ensure-RoadmapIndexJson {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Host "skip missing: $Path"
        return
    }

    Backup-File $Path

    try {
        $raw = Read-Utf8 $Path
        $obj = $raw | ConvertFrom-Json -Depth 100
    }
    catch {
        throw "Invalid JSON in $Path. Repair stopped before writing. Error: $($_.Exception.Message)"
    }

    $obj | Add-Member -NotePropertyName "machine_readable_state" -NotePropertyValue "ROADMAP_CURRENT.json" -Force
    $obj | Add-Member -NotePropertyName "role" -NotePropertyValue "traceability_index" -Force
    $obj | Add-Member -NotePropertyName "authority" -NotePropertyValue "non-prevailing" -Force
    $obj | Add-Member -NotePropertyName "status" -NotePropertyValue "active" -Force

    $currentHorizon = 0
    if ($null -ne $obj.PSObject.Properties["horizon_years"]) {
        [void][int]::TryParse([string]$obj.horizon_years, [ref]$currentHorizon)
    }
    if ($currentHorizon -lt 50) {
        $obj | Add-Member -NotePropertyName "horizon_years" -NotePropertyValue 50 -Force
    }

    foreach ($name in @(
        "canonical_source",
        "canonical_roadmap",
        "canonical_index",
        "machine_readable_canonical_roadmap_index"
    )) {
        if ($null -ne $obj.PSObject.Properties[$name]) {
            $obj.PSObject.Properties.Remove($name)
        }
    }

    $json = $obj | ConvertTo-Json -Depth 100
    $json = $json -replace 'docs/ROADMAP\.md', 'ROADMAP_CANONICAL.md'
    $json = $json -replace 'docs/roadmap/roadmap\.index\.json', 'ROADMAP_CURRENT.json'
    $json = $json -replace 'repo/roadmap/roadmap\.yaml', 'ROADMAP_CURRENT.json'

    Write-Utf8Atomic -Path $Path -Content (($json.TrimEnd()) + "`n")
    Write-Host "fixed roadmap index json: $Path"
}

function Ensure-LegacyYamlNonAuthoritative {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Host "skip missing: $Path"
        return
    }

    Backup-File $Path
    $body = Read-Utf8 $Path
    $body = Normalize-Newlines $body

    $body = [regex]::Replace($body, '(?im)^\s*authority\s*:\s*(prevailing|authoritative|canonical)\s*$', 'authority: non-prevailing')
    $body = [regex]::Replace($body, '(?im)^\s*role\s*:\s*canonical\s*$', 'role: legacy_non_authoritative')
    $body = [regex]::Replace($body, '(?im)^\s*canonical_source\s*:\s*docs/ROADMAP\.md\s*$', 'canonical_source: ROADMAP_CANONICAL.md')
    $body = [regex]::Replace($body, '(?im)^\s*machine_readable_canonical.*roadmap\.index\.json\s*$', 'machine_readable_state: ROADMAP_CURRENT.json')
    $body = $body -replace 'docs/ROADMAP\.md', 'ROADMAP_CANONICAL.md'
    $body = $body -replace 'docs/roadmap/roadmap\.index\.json', 'ROADMAP_CURRENT.json'

    if ($body -notmatch '(?im)^\s*authority\s*:\s*non-prevailing\s*$') {
        $body = "authority: non-prevailing`nrole: legacy_non_authoritative`nmachine_readable_state: ROADMAP_CURRENT.json`n" + $body.TrimStart()
    }

    Write-Utf8Atomic -Path $Path -Content (($body.TrimEnd()) + "`n")
    Write-Host "fixed legacy yaml: $Path"
}

function Run-Gate {
    $gate = Resolve-RepoPath "scripts/run-roadmap-authority-gate.ps1"

    if (-not (Test-Path -LiteralPath $gate)) {
        Write-Warning "Gate script not found: $gate"
        return
    }

    Write-Host ""
    Write-Host "running gate..."
    & pwsh -NoLogo -NoProfile -File $gate
    if ($LASTEXITCODE -ne 0) {
        Write-Host "gate process exit code: $LASTEXITCODE"
    }
}

$canonical = Resolve-RepoPath "ROADMAP_CANONICAL.md"

$derivedMarkdown = @(
    "ROADMAP.md",
    "docs/ROADMAP.md",
    "docs/roadmap/aso-x-integrated-mandatory-roadmap.md"
) | ForEach-Object { Resolve-RepoPath $_ }

$indexJson = Resolve-RepoPath "docs/roadmap/roadmap.index.json"
$legacyYaml = Resolve-RepoPath "repo/roadmap/roadmap.yaml"

Write-Host "repo root: $Root"
Write-Host "repair stamp: $Stamp"
Write-Host ""

Ensure-CanonicalMarkdownMetadata -Path $canonical

foreach ($p in $derivedMarkdown) {
    Ensure-DerivedMarkdownHeader -Path $p
}

Ensure-RoadmapIndexJson -Path $indexJson
Ensure-LegacyYamlNonAuthoritative -Path $legacyYaml

Run-Gate

Write-Host ""
Write-Host "done. Backups were created with suffix: .authorityfix.$Stamp.bak"
