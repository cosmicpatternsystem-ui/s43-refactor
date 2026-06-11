$ErrorActionPreference = "Stop"

function Write-Ok($m){ Write-Host "[OK]   $m" -ForegroundColor Green }
function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn2($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Fail($m){ Write-Host "[FAIL] $m" -ForegroundColor Red }

function Escape-Csv([string]$s){
    if($null -eq $s){ return '""' }
    return '"' + ($s.Replace('"','""')) + '"'
}

$root = Get-Location

$mainFiles = @(
    "s43_instrumented_LATEST.py",
    "s43_latest_refactor.py",
    "MY_S43_LATEST.py"
)

$refFiles = @(
    "11029.py",
    "SAFETY_PROTOCOL.md",
    "SAFETY_PROTOCOL_FINAL_VERIFY_20260608_175301.txt",
    "SAFETY_GATE_MAPPING_PASS1.txt"
)

$patterns = @(
    "_ai_trader",
    "AITrader",
    "AI_TRADER_ENABLE",
    "OPENAI_TRADE_ENABLE",
    "OPENAI_TRADE_ALLOW_ND",
    "autonomous_ai",
    "risk",
    "DAILY_RISK_LIMIT",
    "WEEKLY_RISK_LIMIT",
    "MACRO_EXTREME_OFF_TH",
    "kill",
    "drawdown",
    "parity",
    "gate",
    "safety"
)

Write-Info "Starting SAFE PATCH PROPOSAL scan"
Write-Info "Root: $root"

$missingMain = @()
foreach($f in $mainFiles){
    if(-not (Test-Path $f)){
        $missingMain += $f
    }
}

if($missingMain.Count -gt 0){
    Write-Fail "Missing required main files:"
    foreach($m in $missingMain){
        Write-Host " - $m" -ForegroundColor Red
    }
    Write-Fail "No action was performed on source files."
    exit 1
}

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $root ("safe_patch_proposal_full_" + $ts)
$backupDir = Join-Path $outDir "backup_main3"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

Write-Ok "Output directory created: $outDir"
Write-Ok "Backup directory created: $backupDir"

# Backup main files only
foreach($f in $mainFiles){
    $src = Join-Path $root $f
    $dst = Join-Path $backupDir $f
    Copy-Item -Path $src -Destination $dst -Force
    Write-Ok "Backup copied: $f"
}

# Manifest SHA256
$manifestRows = New-Object System.Collections.Generic.List[string]
$manifestRows.Add("role,file,path,sha256,size_bytes,last_write_time")

foreach($f in $mainFiles){
    $p = Join-Path $root $f
    $h = (Get-FileHash -Algorithm SHA256 -Path $p).Hash
    $item = Get-Item $p
    $manifestRows.Add(
        (Escape-Csv "main") + "," +
        (Escape-Csv $f) + "," +
        (Escape-Csv $p) + "," +
        (Escape-Csv $h) + "," +
        $item.Length + "," +
        (Escape-Csv $item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss"))
    )
}

foreach($f in $refFiles){
    if(Test-Path $f){
        $p = Join-Path $root $f
        $h = (Get-FileHash -Algorithm SHA256 -Path $p).Hash
        $item = Get-Item $p
        $manifestRows.Add(
            (Escape-Csv "reference") + "," +
            (Escape-Csv $f) + "," +
            (Escape-Csv $p) + "," +
            (Escape-Csv $h) + "," +
            $item.Length + "," +
            (Escape-Csv $item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss"))
        )
    }
}

$manifestPath = Join-Path $outDir "FILES_MANIFEST_SHA256.csv"
Set-Content -Path $manifestPath -Value $manifestRows -Encoding UTF8
Write-Ok "Manifest written: $manifestPath"

# Scan function
$csvRows = New-Object System.Collections.Generic.List[string]
$csvRows.Add("role,file,line,pattern,text")

$summary = @{}

function Add-HitsFromFile([string]$role, [string]$filePath){
    Write-Info "Scanning [$role] $filePath"

    if(-not (Test-Path $filePath)){
        Write-Warn2 "File not found, skipped: $filePath"
        return
    }

    $lines = Get-Content -Path $filePath -Encoding UTF8

    for($i = 0; $i -lt $lines.Count; $i++){
        $line = $lines[$i]

        foreach($p in $patterns){
            if($line -match [regex]::Escape($p)){
                $script:csvRows.Add(
                    (Escape-Csv $role) + "," +
                    (Escape-Csv $filePath) + "," +
                    ($i + 1) + "," +
                    (Escape-Csv $p) + "," +
                    (Escape-Csv $line.Trim())
                )

                $key = "$filePath::$p"
                if(-not $script:summary.ContainsKey($key)){
                    $script:summary[$key] = 0
                }
                $script:summary[$key]++
            }
        }
    }
}

foreach($f in $mainFiles){
    Add-HitsFromFile "main" $f
}

foreach($f in $refFiles){
    if(Test-Path $f){
        Add-HitsFromFile "reference" $f
    } else {
        Write-Warn2 "Reference file not found, skipped: $f"
    }
}

$csvPath = Join-Path $outDir "PATCH_HITS.csv"
Set-Content -Path $csvPath -Value $csvRows -Encoding UTF8
Write-Ok "Hit CSV written: $csvPath"

# Build compact summary table
$summaryLines = New-Object System.Collections.Generic.List[string]
$summaryLines.Add("file,pattern,count")

foreach($k in $summary.Keys | Sort-Object){
    $parts = $k -split "::", 2
    $summaryLines.Add(
        (Escape-Csv $parts[0]) + "," +
        (Escape-Csv $parts[1]) + "," +
        $summary[$k]
    )
}

$summaryPath = Join-Path $outDir "PATCH_HIT_SUMMARY.csv"
Set-Content -Path $summaryPath -Value $summaryLines -Encoding UTF8
Write-Ok "Hit summary written: $summaryPath"

# Proposal markdown
$proposal = New-Object System.Collections.Generic.List[string]
$proposal.Add("# SAFE PATCH PROPOSAL - AI/RISK GAP REVIEW")
$proposal.Add("")
$proposal.Add("Generated: $(Get-Date)")
$proposal.Add("")
$proposal.Add("## Safety Statement")
$proposal.Add("")
$proposal.Add("This package does not modify any source code.")
$proposal.Add("It only creates backups, evidence files, scan reports, and a patch proposal.")
$proposal.Add("")
$proposal.Add("## Main Files")
foreach($f in $mainFiles){
    $proposal.Add("- `$f`")
}
$proposal.Add("")
$proposal.Add("## Reference Files Used If Present")
foreach($f in $refFiles){
    if(Test-Path $f){
        $proposal.Add("- `$f` - found")
    } else {
        $proposal.Add("- `$f` - not found / skipped")
    }
}
$proposal.Add("")
$proposal.Add("## Evidence Files")
$proposal.Add("")
$proposal.Add("- `PATCH_HITS.csv`: line-level pattern hits")
$proposal.Add("- `PATCH_HIT_SUMMARY.csv`: hit counts by file and pattern")
$proposal.Add("- `FILES_MANIFEST_SHA256.csv`: source/reference hashes")
$proposal.Add("- `PATCH_NOTES.txt`: review notes")
$proposal.Add("- `OPEN_ME_IN_NOTEPAD.txt`: human-readable quick guide")
$proposal.Add("- `backup_main3/`: backups of main files")
$proposal.Add("")
$proposal.Add("## Recommended Review Order")
$proposal.Add("")
$proposal.Add("1. Open `OPEN_ME_IN_NOTEPAD.txt`.")
$proposal.Add("2. Open `PATCH_HITS.csv` and filter by:")
$proposal.Add("   - `_ai_trader`")
$proposal.Add("   - `OPENAI_TRADE_ENABLE`")
$proposal.Add("   - `OPENAI_TRADE_ALLOW_ND`")
$proposal.Add("   - `AI_TRADER_ENABLE`")
$proposal.Add("   - `autonomous_ai`")
$proposal.Add("   - `risk`")
$proposal.Add("3. Compare the 3 main files.")
$proposal.Add("4. Use `11029.py` only as reference evidence, not as a direct edit target.")
$proposal.Add("5. Prepare manual patch only after line-level confirmation.")
$proposal.Add("")
$proposal.Add("## Current Patch Recommendation")
$proposal.Add("")
$proposal.Add("- Preferred patch base: `s43_instrumented_LATEST.py`")
$proposal.Add("- Reason: it is the instrumented candidate and is better suited for evidence-first debugging.")
$proposal.Add("")
$proposal.Add("## Non-Goals")
$proposal.Add("")
$proposal.Add("- No automatic code rewrite.")
$proposal.Add("- No direct change to source files.")
$proposal.Add("- No behavioral modification.")
$proposal.Add("- No API/model setting injection without confirmed architecture evidence.")

$proposalPath = Join-Path $outDir "PATCH_PROPOSAL.md"
Set-Content -Path $proposalPath -Value $proposal -Encoding UTF8
Write-Ok "Proposal written: $proposalPath"

# Notes file
$notes = New-Object System.Collections.Generic.List[string]
$notes.Add("SAFE PATCH NOTES")
$notes.Add("================")
$notes.Add("")
$notes.Add("Generated: $(Get-Date)")
$notes.Add("Root: $root")
$notes.Add("Output: $outDir")
$notes.Add("")
$notes.Add("This run did NOT modify source files.")
$notes.Add("")
$notes.Add("Backups:")
$notes.Add($backupDir)
$notes.Add("")
$notes.Add("Main review targets:")
$notes.Add("- _ai_trader")
$notes.Add("- AITrader")
$notes.Add("- AI_TRADER_ENABLE")
$notes.Add("- OPENAI_TRADE_ENABLE")
$notes.Add("- OPENAI_TRADE_ALLOW_ND")
$notes.Add("- autonomous_ai")
$notes.Add("- risk and safety gates")
$notes.Add("")
$notes.Add("Recommended base for any future manual patch:")
$notes.Add("- s43_instrumented_LATEST.py")
$notes.Add("")
$notes.Add("Important:")
$notes.Add("- 11029.py should remain reference-only unless you explicitly decide otherwise.")
$notes.Add("- Review PATCH_HITS.csv line-by-line before making any patch.")
$notes.Add("- Keep the ZIP and SHA256 for audit traceability.")

$notesPath = Join-Path $outDir "PATCH_NOTES.txt"
Set-Content -Path $notesPath -Value $notes -Encoding UTF8
Write-Ok "Notes written: $notesPath"

# Notepad guide
$notepad = New-Object System.Collections.Generic.List[string]
$notepad.Add("OPEN THIS FILE IN NOTEPAD")
$notepad.Add("=========================")
$notepad.Add("")
$notepad.Add("SAFE PATCH PROPOSAL PACKAGE CREATED SUCCESSFULLY")
$notepad.Add("")
$notepad.Add("Date:")
$notepad.Add("  $(Get-Date)")
$notepad.Add("")
$notepad.Add("Output folder:")
$notepad.Add("  $outDir")
$notepad.Add("")
$notepad.Add("Source files were NOT modified.")
$notepad.Add("")
$notepad.Add("Backups are here:")
$notepad.Add("  $backupDir")
$notepad.Add("")
$notepad.Add("Read these files in this order:")
$notepad.Add("")
$notepad.Add("1) PATCH_PROPOSAL.md")
$notepad.Add("   Main proposal and review plan.")
$notepad.Add("")
$notepad.Add("2) PATCH_NOTES.txt")
$notepad.Add("   Human-readable notes and next steps.")
$notepad.Add("")
$notepad.Add("3) PATCH_HITS.csv")
$notepad.Add("   Line-level scan evidence.")
$notepad.Add("")
$notepad.Add("4) PATCH_HIT_SUMMARY.csv")
$notepad.Add("   Counts by file and keyword.")
$notepad.Add("")
$notepad.Add("5) FILES_MANIFEST_SHA256.csv")
$notepad.Add("   Hashes for audit/reproducibility.")
$notepad.Add("")
$notepad.Add("Main keywords scanned:")
foreach($p in $patterns){
    $notepad.Add("  - $p")
}
$notepad.Add("")
$notepad.Add("Recommended future patch base:")
$notepad.Add("  s43_instrumented_LATEST.py")
$notepad.Add("")
$notepad.Add("Reminder:")
$notepad.Add("  This is evidence collection only.")
$notepad.Add("  No live patch was applied.")

$notepadPath = Join-Path $outDir "OPEN_ME_IN_NOTEPAD.txt"
Set-Content -Path $notepadPath -Value $notepad -Encoding UTF8
Write-Ok "Notepad guide written: $notepadPath"

# ZIP output
$zipPath = Join-Path $root ("safe_patch_proposal_full_" + $ts + ".zip")
Compress-Archive -Path (Join-Path $outDir "*") -DestinationPath $zipPath -Force
Write-Ok "ZIP created: $zipPath"

$zipSha = (Get-FileHash -Algorithm SHA256 -Path $zipPath).Hash
$zipShaPath = $zipPath + ".sha256.txt"
Set-Content -Path $zipShaPath -Value $zipSha -Encoding ASCII
Write-Ok "ZIP SHA256 written: $zipShaPath"

Write-Host ""
Write-Host "================ FINAL STATUS ================" -ForegroundColor White
Write-Host "SAFE PATCH PROPOSAL FULL COMPLETED" -ForegroundColor Green
Write-Host "SOURCE MODIFIED = NO" -ForegroundColor Green
Write-Host "OUT_DIR         = $outDir" -ForegroundColor White
Write-Host "NOTEPAD_FILE    = $notepadPath" -ForegroundColor White
Write-Host "ZIP_FILE        = $zipPath" -ForegroundColor White
Write-Host "ZIP_SHA256      = $zipSha" -ForegroundColor White
Write-Host "=============================================" -ForegroundColor White
Write-Host ""

try {
    Start-Process notepad.exe $notepadPath
    Write-Ok "Opened Notepad file."
} catch {
    Write-Warn2 "Could not open Notepad automatically. Open this file manually:"
    Write-Host $notepadPath -ForegroundColor Yellow
}
