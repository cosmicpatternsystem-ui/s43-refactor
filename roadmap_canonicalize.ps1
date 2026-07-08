#requires -Version 5.1
<#
.SYNOPSIS
  ASO-X Roadmap Canonicalization (Phase 22.13) - CORRECTED.
  Run as a FILE, never paste into the console (param/Stop scoping breaks).
.NOTES
  Idempotent. Non-destructive (archive + tombstone). BOM-free UTF-8 / LF.
#>
[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-RepoFile {
    param([string]$Path, [string]$Content)
    $normalized = ($Content -replace "`r`n", "`n") -replace "`r", "`n"
    if ($DryRun) { Write-Host ("[DRYRUN] would write {0}" -f $Path); return }
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    [System.IO.File]::WriteAllText($Path, $normalized, $Utf8NoBom)
    Write-Host ("[WRITE]   {0}" -f $Path)
}

function Invoke-ArchiveLegacy {
    param([string]$Path, [string]$Reason, [string]$Stamp)
    if (-not (Test-Path $Path)) { Write-Host ("[SKIP]    absent: {0}" -f $Path); return }
    $archDir = Join-Path $RepoRoot ('.roadmap_archive\' + $Stamp)
    $rel  = $Path.Substring($RepoRoot.Length).TrimStart('\','/')
    $dest = Join-Path $archDir $rel
    if ($DryRun) { Write-Host ("[DRYRUN] would archive {0}  ({1})" -f $rel, $Reason); return }
    $destDir = Split-Path -Parent $dest
    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Force -Path $destDir | Out-Null }
    Move-Item -LiteralPath $Path -Destination $dest -Force
    $tomb = ("RETIRED {0}`nreason : {1}`narchive: {2}`n" -f $Stamp, $Reason, $dest)
    Write-RepoFile -Path ($Path + '.RETIRED.txt') -Content $tomb
    Write-Host ("[ARCHIVE] {0}  ({1})" -f $rel, $Reason)
}

Set-Location $RepoRoot
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
Write-Host "=== ASO-X Roadmap Canonicalization (corrected) ==="
Write-Host ("RepoRoot: {0}  DryRun: {1}  Stamp: {2}" -f $RepoRoot, [bool]$DryRun, $stamp)
Write-Host ""

# --- STEP 1: write the corrected guard (this is the actual fix) -------------
$guard = @'
#!/usr/bin/env python3
"""ASO-X roadmap guard.

Single source of truth: ROADMAP_CURRENT.json at repo root.
Schema is the one emitted by scripts/update-roadmap.ps1 and enforced by
scripts/validate-roadmap.ps1. Keep all three in lockstep.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROADMAP_PATH = Path("ROADMAP_CURRENT.json")
SOURCE_OF_TRUTH = "repository phase documents"
MIN_SCHEMA_VERSION = 2

REQUIRED = (
    "schema_version",
    "source_of_truth",
    "generated_by",
    "enforcement_model",
    "updated_at_utc",
    "phase_count",
    "operational_metadata_schema",
    "phases",
)


def fail(msg):
    sys.stdout.write("roadmap_guard: FAIL: " + msg + "\n")
    raise SystemExit(1)


def main():
    if not ROADMAP_PATH.exists():
        fail("missing " + str(ROADMAP_PATH))

    try:
        data = json.loads(ROADMAP_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail("invalid JSON: " + str(exc))

    missing = [k for k in REQUIRED if k not in data]
    if missing:
        fail("missing fields: " + ", ".join(missing))

    sv = data.get("schema_version")
    if isinstance(sv, bool) or not isinstance(sv, int) or sv < MIN_SCHEMA_VERSION:
        fail("schema_version must be int >= %d, got %r" % (MIN_SCHEMA_VERSION, sv))

    if data.get("source_of_truth") != SOURCE_OF_TRUTH:
        fail("source_of_truth must be %r" % SOURCE_OF_TRUTH)

    phases = data.get("phases")
    if not isinstance(phases, list):
        fail("phases must be an array")

    pc = data.get("phase_count")
    if not isinstance(pc, int) or pc != len(phases):
        fail("phase_count (%r) != len(phases) (%d)" % (pc, len(phases)))

    sys.stdout.write("roadmap_guard: OK (%d phases)\n" % len(phases))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'@
Write-RepoFile -Path (Join-Path $RepoRoot 'scripts\roadmap_guard.py') -Content $guard
Invoke-ArchiveLegacy -Path (Join-Path $RepoRoot 'tools\ai\roadmap_guard.py') -Reason 'duplicate guard, superseded by scripts/roadmap_guard.py' -Stamp $stamp

# --- STEP 2: finish defusing the time-bombs (the ones that failed earlier) --
Invoke-ArchiveLegacy -Path (Join-Path $RepoRoot 'tools\validate_roadmap_state.py')  -Reason 'hardcoded current_phase 22.13' -Stamp $stamp
Invoke-ArchiveLegacy -Path (Join-Path $RepoRoot 'tools\assert_no_stale_roadmap.py') -Reason 'hardcoded stale phase 22.12'  -Stamp $stamp
Invoke-ArchiveLegacy -Path (Join-Path $RepoRoot 'validate_roadmap_state.py')        -Reason 'legacy baseline_commit 0ad415a' -Stamp $stamp
Invoke-ArchiveLegacy -Path (Join-Path $RepoRoot 'roadmap_sync.py')                  -Reason 'legacy baseline_commit 0ad415a' -Stamp $stamp

# --- STEP 3: finish archiving frozen / divergent artifacts ------------------
Invoke-ArchiveLegacy -Path (Join-Path $RepoRoot 'docs\governance\ROADMAP_CURRENT.json')    -Reason 'orphan B-schema, no live generator' -Stamp $stamp
Invoke-ArchiveLegacy -Path (Join-Path $RepoRoot 'AUDIT\ROADMAP_CURRENT.json')              -Reason 'legacy A-schema current_phase 22.13' -Stamp $stamp
Invoke-ArchiveLegacy -Path (Join-Path $RepoRoot 'ROADMAP\ROADMAP_STATE.json')              -Reason 'legacy A-schema baseline_commit 0ad415a' -Stamp $stamp
Invoke-ArchiveLegacy -Path (Join-Path $RepoRoot 'ROADMAP_CURRENT.governance-backup.json')  -Reason 'leg
