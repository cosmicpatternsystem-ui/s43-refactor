[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [string]$OutFile = "",
    [switch]$IncludeJsonPreview
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Utf8NoBomLf {
    param([string]$Path, [string]$Content)
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    $normalized = $Content -replace "`r`n", "`n" -replace "`r", "`n"
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $normalized, $utf8NoBom)
}

function Add-Section { param($Lines, $Title) $Lines.Add(""); $Lines.Add(("=" * 80)); $Lines.Add($Title); $Lines.Add(("=" * 80)) }
function Add-Line { param($Lines, $Text) $Lines.Add($Text) }

function Resolve-RepoRoot {
    param([string]$Hint)
    if ($Hint -and (Test-Path -LiteralPath $Hint)) { return (Resolve-Path -LiteralPath $Hint).Path }
    return (Get-Location).Path
}

$repo = Resolve-RepoRoot -Hint $RepoRoot
if (-not $OutFile) { $OutFile = Join-Path $repo "governance\reports\audit_diagnostics.txt" }
$lines = New-Object 'System.Collections.Generic.List[string]'

Add-Section $lines "AUDIT DIAGNOSTICS"
Add-Line $lines ("Timestamp: " + (Get-Date).ToString("yyyy-MM-dd HH:mm:ssK"))
Add-Line $lines ("ResolvedRepoRoot: " + $repo)

Add-Section $lines "GIT STATUS"
$gitStatus = & git -C $repo status --short 2>&1 | Out-String
Add-Line $lines $gitStatus

Add-Section $lines "SCRIPT CHECK"
$scriptPath = Join-Path $repo "governance\scripts\Rebuild-Audit.ps1"
if (Test-Path $scriptPath) {
    Add-Line $lines "Rebuild-Audit.ps1 exists."
    $f = Get-Item $scriptPath
    Add-Line $lines ("Size: " + $f.Length + " bytes")
} else {
    Add-Line $lines "Rebuild-Audit.ps1 NOT FOUND."
}

Add-Section $lines "DONE"
$text = [string]::Join("`n", $lines)
Write-Utf8NoBomLf -Path $OutFile -Content $text
Write-Host "Diagnostics written to: $OutFile"
