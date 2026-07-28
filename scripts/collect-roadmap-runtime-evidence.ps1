# PowerShell 5 compatible - low memory version
[CmdletBinding()]
param(
  [string]$OutRoot = "docs/governance/evidence/runtime-assessment",
  [switch]$IncludeFileBodies,
  [int]$MaxMatchesPerTerm = 40
)

$ErrorActionPreference = "Stop"

function Write-Utf8NoBom {
  param([string]$Path,[string]$Content)
  $dir = Split-Path -Parent $Path
  if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  if ($null -eq $Content) { $Content = "" }
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, ($Content -replace "`r`n","`n"), $enc)
}

function Get-Sha256 {
  param([string]$Path)
  if (Test-Path -LiteralPath $Path) { return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash }
  return $null
}

$repoRoot = (git rev-parse --show-toplevel 2>$null)
if (-not $repoRoot) { $repoRoot = (Get-Location).Path }
$repoRoot = $repoRoot.Trim()
Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path $OutRoot $timestamp
$commandsDir = Join-Path $outDir "commands"
$filesDir = Join-Path $outDir "files"
$searchDir = Join-Path $outDir "search"
New-Item -ItemType Directory -Force -Path $outDir,$commandsDir,$filesDir,$searchDir | Out-Null

$gitStatus = git status --short 2>&1 | Out-String
$gitBranch = git branch --show-current 2>&1 | Out-String
$gitLog = git log --oneline -n 20 2>&1 | Out-String
$pyVer = python --version 2>&1 | Out-String
$psVer = $PSVersionTable | Out-String

Write-Utf8NoBom (Join-Path $commandsDir "git_status_short.txt") $gitStatus
Write-Utf8NoBom (Join-Path $commandsDir "git_branch.txt") $gitBranch
Write-Utf8NoBom (Join-Path $commandsDir "git_log_recent.txt") $gitLog
Write-Utf8NoBom (Join-Path $commandsDir "python_version.txt") $pyVer
Write-Utf8NoBom (Join-Path $commandsDir "powershell_version.txt") $psVer

$keyFiles = @(
  "scripts/resolve_next_action.py",
  "scripts/update-roadmap.ps1",
  "scripts/roadmap_generator.py",
  "scripts/roadmap_guard.py",
  "scripts/validate-roadmap.ps1",
  "scripts/validate-roadmap-authority.ps1",
  "scripts/run-roadmap-authority-gate.ps1",
  "scripts/reject-roadmap-shadow-authorities.ps1",
  "docs/governance/ROADMAP_CURRENT.json",
  "docs/governance/ROADMAP_CANONICAL.md",
  "docs/governance/CANONICAL_ROADMAP_DECLARATION.md",
  "docs/governance/ROADMAP_CONSTITUTION.md",
  "docs/governance/ROADMAP_MANIFEST.json",
  "docs/governance/COMMERCIAL_READINESS_STATE.json"
)

$report = @()
foreach ($f in $keyFiles) {
  $exists = Test-Path -LiteralPath $f
  $obj = [ordered]@{ path=$f; exists=$exists; bytes=$null; sha256=$null }
  if ($exists) {
    $gi = Get-Item -LiteralPath $f
    $obj.bytes = $gi.Length
    $obj.sha256 = Get-Sha256 $f
    if ($IncludeFileBodies -and $gi.Length -le 512000) {
      $name = $f.Replace("\","__").Replace("/","__")
      $target = Join-Path $filesDir $name
      $body = Get-Content -LiteralPath $f -Raw
      Write-Utf8NoBom $target $body
    }
  }
  $report += New-Object psobject -Property $obj
}
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outDir "key_files.json") -Encoding UTF8

$inventory = @()
$patterns = @(
  "scripts\*roadmap*",
  "scripts\*resolve*",
  "scripts\*authority*",
  "scripts\*guard*",
  "scripts\*validate*",
  "scripts\*state*",
  "scripts\*ledger*",
  "scripts\*evidence*",
  "docs\governance\*ROADMAP*",
  "docs\governance\*AUTHORITY*",
  "docs\governance\*STATE*",
  "docs\governance\*MANIFEST*",
  "docs\governance\*READINESS*",
  "docs\governance\*CONTRACT*",
  "docs\governance\*HOLD*"
)
foreach ($p in $patterns) {
  Get-ChildItem -Path $p -File -ErrorAction SilentlyContinue | ForEach-Object {
    $inventory += New-Object psobject -Property ([ordered]@{
      path = $_.FullName.Replace($repoRoot + "\", "")
      bytes = $_.Length
      sha256 = (Get-Sha256 $_.FullName)
    })
  }
}
$inventory = $inventory | Sort-Object path -Unique
$inventory | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outDir "inventory.json") -Encoding UTF8
$inventoryMd = "# Runtime/Governance Inventory`r`n`r`n"
foreach ($i in $inventory) {
  $inventoryMd += "- ``" + $i.path + "`` | bytes=" + $i.bytes + " | sha256=" + $i.sha256 + "`r`n"
}
Write-Utf8NoBom (Join-Path $outDir "inventory.md") $inventoryMd

$terms = @("HOLD","HOLD_ACTIVE","CONTROLLED_BLOCKED","CONTRACT_MISMATCH","BLOCKED","forbidden_actions","allowed_actions","unblock","exit_criteria","stale","authority","shadow authority","NEXT_ACTION","STATUS_CLASSIFICATION","ROADMAP_CURRENT","COMMERCIAL_READINESS_STATE")
$roots = @("scripts","docs/governance")
$summary = @()
$semanticMd = "# Semantic Search Summary`r`n`r`n"
foreach ($t in $terms) {
  $count = 0
  $sample = New-Object System.Collections.ArrayList
  foreach ($r in $roots) {
    if (Test-Path $r) {
      Get-ChildItem -Path $r -Recurse -File -ErrorAction SilentlyContinue | Select-String -SimpleMatch $t -ErrorAction SilentlyContinue | ForEach-Object {
        $count++
        if ($sample.Count -lt $MaxMatchesPerTerm) {
          [void]$sample.Add(($_.Path.Replace($repoRoot + "\", "")) + ":" + $_.LineNumber + ": " + $_.Line.Trim())
        }
      }
    }
  }
  $obj = New-Object psobject -Property ([ordered]@{
    term = $t
    count = $count
    sample_count = $sample.Count
    truncated = ($count -gt $sample.Count)
  })
  $summary += $obj
  $safe = ($t -replace "[^A-Za-z0-9_.-]","_") + ".txt"
  $content = @()
  $content += "TERM: $t"
  $content += "COUNT: $count"
  $content += "SAMPLE_COUNT: $($sample.Count)"
  $content += "TRUNCATED: " + ([string]($count -gt $sample.Count))
  $content += ""
  $content += $sample
  Write-Utf8NoBom (Join-Path $searchDir $safe) ($content -join "`r`n")
  $semanticMd += "## $t`r`n"
  $semanticMd += "- count: $count`r`n"
  $semanticMd += "- sample_count: $($sample.Count)`r`n"
  $semanticMd += "- truncated: " + ([string]($count -gt $sample.Count)) + "`r`n`r`n"
}
$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outDir "semantic_search.json") -Encoding UTF8
Write-Utf8NoBom (Join-Path $outDir "semantic_search.md") $semanticMd

$index = @()
$index += "# ASO-X Runtime Evidence Snapshot"
$index += ""
$index += "Generated: $(Get-Date -Format s)"
$index += ""
$index += "Repo Root: $repoRoot"
$index += ""
$index += "Output Dir: $outDir"
$index += ""
$index += "Safety:"
$index += "- Read-only collection against repo content"
$index += "- No git add/commit/push"
$index += "- No network"
$index += "- No resolver execution in this PS5-safe mode"
$index += ""
$index += "Share next:"
$index += "- assessment_hints.json"
$index += "- semantic_search.json"
$index += "- semantic_search.md"
$index += "- key_files.json"
$index += "- inventory.md"
$index += ""
Write-Utf8NoBom (Join-Path $outDir "ASO_X_RUNTIME_EVIDENCE_INDEX.md") ($index -join "`r`n")

$assessment = [ordered]@{
  generated_at = (Get-Date -Format s)
  repo_root = $repoRoot
  out_dir = $outDir
  powershell_edition = $PSVersionTable.PSEdition
  powershell_version = $PSVersionTable.PSVersion.ToString()
  resolver_file_exists = (Test-Path "scripts/resolve_next_action.py")
  roadmap_current_exists = (Test-Path "docs/governance/ROADMAP_CURRENT.json")
  roadmap_manifest_exists = (Test-Path "docs/governance/ROADMAP_MANIFEST.json")
  commercial_readiness_state_exists = (Test-Path "docs/governance/COMMERCIAL_READINESS_STATE.json")
  next_step = "Send generated evidence files to reviewer"
}
$assessment | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outDir "assessment_hints.json") -Encoding UTF8

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Output: $outDir" -ForegroundColor Cyan
Write-Host "Send these files:" -ForegroundColor Cyan
Write-Host "  $outDir\ASO_X_RUNTIME_EVIDENCE_INDEX.md"
Write-Host "  $outDir\assessment_hints.json"
Write-Host "  $outDir\semantic_search.json"
Write-Host "  $outDir\semantic_search.md"
Write-Host "  $outDir\key_files.json"
Write-Host "  $outDir\inventory.md"
