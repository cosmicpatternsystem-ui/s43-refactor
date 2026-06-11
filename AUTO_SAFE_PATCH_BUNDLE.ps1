$ErrorActionPreference = "Stop"

function Write-Ok($msg)   { Write-Host "[OK]  $msg" -ForegroundColor Green }
function Write-Info($msg) { Write-Host "[..]  $msg" -ForegroundColor Cyan }
function Write-Warn2($msg){ Write-Host "[!!]  $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "[ERR] $msg" -ForegroundColor Red }

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$root = Get-Location
$outDir = Join-Path $root ("auto_safe_patch_bundle_" + $ts)
$backupDir = Join-Path $outDir "backup"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

$targets = @(
  "s43_instrumented_LATEST.py",
  "s43_latest_refactor.py",
  "MY_S43_LATEST.py"
)

$refs = @(
  "11029.py",
  "SAFETY_PROTOCOL.md",
  "SAFETY_GATE_MAPPING_PASS1.txt"
)

$allFiles = @()
$allFiles += $targets
$allFiles += $refs
$allFiles = $allFiles | Select-Object -Unique

$patterns = @(
  "_ai_trader",
  "AI_TRADER_ENABLE",
  "AITrader",
  "autonomous_ai",
  "OPENAI_TRADE_ENABLE",
  "OPENAI_TRADE_ALLOW_ND",
  "OPENAI_API_KEY",
  "OpenAI(",
  "AsyncOpenAI(",
  "chat.completions",
  "responses.create",
  "default_model",
  "base_url",
  "risk",
  "drawdown",
  "kill",
  "gate",
  "safety",
  "DAILY_RISK_LIMIT",
  "WEEKLY_RISK_LIMIT",
  "MACRO_EXTREME_OFF_TH",
  "CapitalKillSwitch"
)

$manifest = New-Object System.Collections.Generic.List[object]
$hits = New-Object System.Collections.Generic.List[object]
$summary = New-Object System.Collections.Generic.List[object]

foreach ($f in $allFiles) {
  if (Test-Path $f) {
    $fi = Get-Item $f
    $hash = (Get-FileHash $f -Algorithm SHA256).Hash
    $manifest.Add([pscustomobject]@{
      file = $fi.Name
      bytes = $fi.Length
      modified = $fi.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
      sha256 = $hash
    }) | Out-Null
    Write-Ok "Found: $f"
  } else {
    $manifest.Add([pscustomobject]@{
      file = $f
      bytes = ""
      modified = ""
      sha256 = "MISSING"
    }) | Out-Null
    Write-Warn2 "Missing: $f"
  }
}

foreach ($f in $targets) {
  if (Test-Path $f) {
    Copy-Item $f -Destination (Join-Path $backupDir ([IO.Path]::GetFileName($f))) -Force
  }
}
Write-Ok "Backups created"

foreach ($f in $allFiles) {
  if (-not (Test-Path $f)) { continue }

  $content = Get-Content $f
  $lineNo = 0
  foreach ($line in $content) {
    $lineNo++
    foreach ($p in $patterns) {
      if ($line -match [regex]::Escape($p)) {
        $hits.Add([pscustomobject]@{
          file = $f
          line = $lineNo
          pattern = $p
          text = $line.Trim()
        }) | Out-Null
      }
    }
  }

  foreach ($p in $patterns) {
    $count = ($hits | Where-Object { $_.file -eq $f -and $_.pattern -eq $p }).Count
    if ($count -gt 0) {
      $summary.Add([pscustomobject]@{
        file = $f
        pattern = $p
        count = $count
      }) | Out-Null
    }
  }
  Write-Info "Scanned: $f"
}

$manifestPath = Join-Path $outDir "FILES_MANIFEST_SHA256.csv"
$hitsPath = Join-Path $outDir "PATCH_HITS.csv"
$summaryPath = Join-Path $outDir "PATCH_HIT_SUMMARY.csv"
$proposalPath = Join-Path $outDir "PATCH_PROPOSAL.md"
$notesPath = Join-Path $outDir "PATCH_NOTES.txt"
$openPath = Join-Path $outDir "OPEN_ME_IN_NOTEPAD.txt"
$diffPath = Join-Path $outDir "FINAL_PATCH_PROPOSAL.diff"

$manifest | Export-Csv -NoTypeInformation -Encoding UTF8 $manifestPath
$hits | Export-Csv -NoTypeInformation -Encoding UTF8 $hitsPath
$summary | Export-Csv -NoTypeInformation -Encoding UTF8 $summaryPath

$proposal = New-Object System.Collections.Generic.List[string]
$proposal.Add("# AUTO SAFE PATCH PROPOSAL") | Out-Null
$proposal.Add("") | Out-Null
$proposal.Add("Generated: $ts") | Out-Null
$proposal.Add("") | Out-Null
$proposal.Add("## Safety Rules") | Out-Null
$proposal.Add("- Keep AUTONOMOUS_AI default-off as required by SAFETY_PROTOCOL.md.") | Out-Null
$proposal.Add("- Do not allow any execution path to bypass risk gates.") | Out-Null
$proposal.Add("- Do not patch python sources automatically without line-level confirmation.") | Out-Null
$proposal.Add("") | Out-Null
$proposal.Add("## Evidence-Based Findings") | Out-Null

$topFindings = $summary | Sort-Object file, pattern
foreach ($row in $topFindings) {
  $proposal.Add("- " + $row.file + " | " + $row.pattern + " = " + $row.count) | Out-Null
}

$proposal.Add("") | Out-Null
$proposal.Add("## Proposed Safe Patch Strategy") | Out-Null
$proposal.Add("1. Use s43_instrumented_LATEST.py as the primary patch base.") | Out-Null
$proposal.Add("2. Keep AI execution fail-closed unless all risk gates pass.") | Out-Null
$proposal.Add("3. Require explicit enablement for autonomous AI and non-default trading.") | Out-Null
$proposal.Add("4. Preserve drawdown, kill-switch, daily and weekly risk ceilings.") | Out-Null
$proposal.Add("5. Apply source patch only after exact AI wiring lines are confirmed.") | Out-Null
$proposal.Add("") | Out-Null
$proposal.Add("## Current Decision") | Out-Null
$proposal.Add("No direct python patch applied. This bundle is evidence-only and fail-closed.") | Out-Null

Set-Content -Path $proposalPath -Value $proposal -Encoding UTF8

$notes = New-Object System.Collections.Generic.List[string]
$notes.Add("AUTO SAFE PATCH BUNDLE") | Out-Null
$notes.Add("Directory: $outDir") | Out-Null
$notes.Add("Backups: $backupDir") | Out-Null
$notes.Add("Manifest: $manifestPath") | Out-Null
$notes.Add("Hits: $hitsPath") | Out-Null
$notes.Add("Summary: $summaryPath") | Out-Null
$notes.Add("Proposal: $proposalPath") | Out-Null
$notes.Add("Diff Proposal: $diffPath") | Out-Null
$notes.Add("Mode: No direct source changes") | Out-Null
Set-Content -Path $notesPath -Value $notes -Encoding UTF8

$openText = New-Object System.Collections.Generic.List[string]
$openText.Add("OPEN THIS FOLDER REVIEW ORDER") | Out-Null
$openText.Add("") | Out-Null
$openText.Add("1) PATCH_PROPOSAL.md") | Out-Null
$openText.Add("2) PATCH_HIT_SUMMARY.csv") | Out-Null
$openText.Add("3) PATCH_HITS.csv") | Out-Null
$openText.Add("4) FILES_MANIFEST_SHA256.csv") | Out-Null
$openText.Add("5) FINAL_PATCH_PROPOSAL.diff") | Out-Null
$openText.Add("") | Out-Null
$openText.Add("This package did NOT modify any python file.") | Out-Null
Set-Content -Path $openPath -Value $openText -Encoding UTF8

$diff = New-Object System.Collections.Generic.List[string]
$diff.Add("--- a/s43_instrumented_LATEST.py") | Out-Null
$diff.Add("+++ b/s43_instrumented_LATEST.py") | Out-Null
$diff.Add("@@ SAFE-PATCH-PROPOSAL @@") | Out-Null
$diff.Add("+ # Proposed only: enforce fail-closed AI gate") | Out-Null
$diff.Add("+ # Proposed only: require AUTONOMOUS_AI explicit opt-in") | Out-Null
$diff.Add("+ # Proposed only: require OPENAI_TRADE_ENABLE and OPENAI_TRADE_ALLOW_ND") | Out-Null
$diff.Add("+ # Proposed only: deny execution on drawdown / kill-switch / daily-weekly risk breach") | Out-Null
$diff.Add("+ # No source modification performed by this bundle") | Out-Null
Set-Content -Path $diffPath -Value $diff -Encoding UTF8

$zipPath = Join-Path $root ("auto_safe_patch_bundle_" + $ts + ".zip")
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path $outDir -DestinationPath $zipPath -Force
$zipHash = (Get-FileHash $zipPath -Algorithm SHA256).Hash
Set-Content -Path ($zipPath + ".sha256.txt") -Value $zipHash -Encoding ASCII

Write-Ok "Bundle directory: $outDir"
Write-Ok "ZIP: $zipPath"
Write-Ok "ZIP SHA256: $zipHash"

try {
  Start-Process notepad.exe $openPath | Out-Null
  Write-Ok "Opened in Notepad: $openPath"
} catch {
  Write-Warn2 "Could not open Notepad automatically"
}
