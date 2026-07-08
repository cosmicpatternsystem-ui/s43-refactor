$ErrorActionPreference = 'Stop'
$RepoRoot = (Get-Location).Path
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$enc = New-Object System.Text.UTF8Encoding($false)

$targets = @(
  @{ Path = 'tools\ai\roadmap_guard.py';                 Reason = 'duplicate guard superseded by scripts/roadmap_guard.py' }
  @{ Path = 'tools\validate_roadmap_state.py';           Reason = 'hardcoded current_phase 22.13' }
  @{ Path = 'tools\assert_no_stale_roadmap.py';          Reason = 'hardcoded stale phase 22.12' }
  @{ Path = 'validate_roadmap_state.py';                 Reason = 'legacy baseline_commit 0ad415a' }
  @{ Path = 'roadmap_sync.py';                           Reason = 'legacy baseline_commit 0ad415a' }
  @{ Path = 'docs\governance\ROADMAP_CURRENT.json';      Reason = 'orphan B-schema, no live generator' }
  @{ Path = 'AUDIT\ROADMAP_CURRENT.json';                Reason = 'legacy A-schema current_phase 22.13' }
  @{ Path = 'ROADMAP\ROADMAP_STATE.json';                Reason = 'legacy A-schema baseline_commit 0ad415a' }
  @{ Path = 'ROADMAP_CURRENT.governance-backup.json';    Reason = 'legacy backup' }
)

foreach ($t in $targets) {
  $src = Join-Path $RepoRoot $t.Path
  if (-not (Test-Path -LiteralPath $src)) { Write-Host "[SKIP]    $($t.Path)"; continue }
  $dest = Join-Path $RepoRoot (".roadmap_archive\$stamp\" + $t.Path)
  $destDir = Split-Path -Parent $dest
  if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Force -Path $destDir | Out-Null }
  Move-Item -LiteralPath $src -Destination $dest -Force
  $tomb = ("RETIRED $stamp`nreason : $($t.Reason)`narchive: $dest`n") -replace "`r`n", "`n"
  [System.IO.File]::WriteAllText($src + '.RETIRED.txt', $tomb, $enc)
  Write-Host "[ARCHIVE] $($t.Path)"
}
Write-Host "Done."
