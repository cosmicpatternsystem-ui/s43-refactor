$ErrorActionPreference = "Stop"

function Save-Text {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

$repoRoot = "E:\saead\ssl\s43_refactor"
Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$utcStamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$evidenceDir = Join-Path $repoRoot "evidence\phase17\runtime_audit\$timestamp"
New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null

$summaryPath = Join-Path $evidenceDir "precheck_summary.txt"
$gitStatusPath = Join-Path $evidenceDir "git_status.txt"
$gitLogPath = Join-Path $evidenceDir "git_log.txt"
$fileInventoryPath = Join-Path $evidenceDir "runtime_file_inventory.txt"
$entrypointScanPath = Join-Path $evidenceDir "entrypoint_scan.txt"
$pythonVersionPath = Join-Path $evidenceDir "python_version.txt"
$hashesPath = Join-Path $evidenceDir "key_file_hashes.txt"

$branch = (git branch --show-current).Trim()
$head = (git rev-parse --short HEAD).Trim()
$origin = (git rev-parse --short origin/phase17-controlled-development).Trim()
$statusShort = git status --short | Out-String
$statusFull = git status | Out-String
$gitLog = git log --oneline -5 | Out-String

Save-Text -Path $gitStatusPath -Content $statusFull
Save-Text -Path $gitLogPath -Content $gitLog

$targets = @(
    "s43.py",
    "s43_instrumented_LATEST.py",
    "MY_S43_LATEST.py",
    "docs\phase17\PHASE17_RUNTIME_AUDIT.md",
    "checklists\PHASE17_RUNTIME_AUDIT_CHECKLIST.md",
    "SAFETY_PROTOCOL.md"
)

$inventory = New-Object System.Collections.Generic.List[string]
$inventory.Add("PHASE17 RUNTIME FILE INVENTORY")
$inventory.Add("UTC=$utcStamp")
$inventory.Add("REPO=$repoRoot")
$inventory.Add("")

foreach ($rel in $targets) {
    $full = Join-Path $repoRoot $rel
    if (Test-Path $full) {
        $item = Get-Item $full
        $inventory.Add("FOUND`t$rel`t$($item.Length)`t$($item.LastWriteTimeUtc.ToString("yyyy-MM-ddTHH:mm:ssZ"))")
    } else {
        $inventory.Add("MISSING`t$rel")
    }
}
Save-Text -Path $fileInventoryPath -Content ($inventory -join [Environment]::NewLine)

$scan = New-Object System.Collections.Generic.List[string]
$scan.Add("PHASE17 ENTRYPOINT SCAN")
$scan.Add("UTC=$utcStamp")
$scan.Add("")

$pythonTargets = @("s43.py","s43_instrumented_LATEST.py","MY_S43_LATEST.py")
foreach ($rel in $pythonTargets) {
    $full = Join-Path $repoRoot $rel
    $scan.Add("===== FILE: $rel =====")
    if (Test-Path $full) {
        $matches = Select-String -Path $full -Pattern '__main__','argparse','sys\.argv','PHOENIX_SELFTEST','live','trade','broker','exchange' -CaseSensitive:$false
        if ($matches) {
            foreach ($m in $matches | Select-Object -First 80) {
                $scan.Add(("{0}:{1}: {2}" -f $rel, $m.LineNumber, $m.Line.Trim()))
            }
        } else {
            $scan.Add("NO_MATCHES")
        }
    } else {
        $scan.Add("FILE_MISSING")
    }
    $scan.Add("")
}
Save-Text -Path $entrypointScanPath -Content ($scan -join [Environment]::NewLine)

try {
    $pythonVersion = (& python --version) 2>&1 | Out-String
} catch {
    $pythonVersion = "python command not available"
}
Save-Text -Path $pythonVersionPath -Content $pythonVersion

$hashLines = New-Object System.Collections.Generic.List[string]
$hashLines.Add("PHASE17 KEY FILE HASHES")
$hashLines.Add("UTC=$utcStamp")
$hashLines.Add("")
foreach ($rel in $targets) {
    $full = Join-Path $repoRoot $rel
    if (Test-Path $full) {
        $h = Get-FileHash -Algorithm SHA256 -Path $full
        $hashLines.Add("$rel`t$($h.Hash)")
    } else {
        $hashLines.Add("$rel`tMISSING")
    }
}
Save-Text -Path $hashesPath -Content ($hashLines -join [Environment]::NewLine)

$summary = @"
PHASE17_RUNTIME_AUDIT_PRECHECK_PASS
UTC=$utcStamp
BRANCH=$branch
HEAD=$head
ORIGIN_PHASE17=$origin
WORKTREE_CLEAN=$([string]::IsNullOrWhiteSpace($statusShort))
EVIDENCE_DIR=$evidenceDir
FILES:
- $summaryPath
- $gitStatusPath
- $gitLogPath
- $fileInventoryPath
- $entrypointScanPath
- $pythonVersionPath
- $hashesPath

NOTE:
- This precheck is read-only.
- No trading runtime was started.
- No live execution was enabled.
"@

Save-Text -Path $summaryPath -Content $summary

Write-Host "PHASE17_RUNTIME_AUDIT_PRECHECK_PASS" -ForegroundColor Green
Write-Host "EVIDENCE_DIR=$evidenceDir"
Write-Host "BRANCH=$branch"
Write-Host "HEAD=$head"
Write-Host "ORIGIN_PHASE17=$origin"
Write-Host "WORKTREE_CLEAN=$([string]::IsNullOrWhiteSpace($statusShort))"