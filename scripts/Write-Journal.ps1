<#
.SYNOPSIS
    Write atomic journal entry for roadmap operations
.DESCRIPTION
    Appends BOM-free UTF-8 JSONL entries to daily log files in data/journal/.
    Part of Phase B.2 Durability - 50-year audit trail

    Fix list vs original:
      1. BOM-free  : [System.Text.UTF8Encoding]::new($false)
      2. UTC time  : (Get-Date).ToUniversalTime() + InvariantCulture
      3. JSONL     : daily append-mode file (YYYYMMDD.jsonl) instead of per-event files
      4. Path fix  : $PSScriptRoot-based resolution (no hardcoded paths)
      5. Append    : FileStream append with FileShare.Read
      6. Flush     : Flush($true) for stronger durability
      7. Retry     : bounded retry with exponential backoff
.PARAMETER Operation
    Operation type: update, restore, checkpoint, init
.PARAMETER Phase
    Phase ID being modified (e.g., "22.13")
.PARAMETER OldStateHash
    SHA256 of previous roadmap.json state
.PARAMETER NewStateHash
    SHA256 of new roadmap.json state
.PARAMETER Status
    Operation result: success, failed, rollback
.PARAMETER DurationMs
    Operation duration in milliseconds
#>
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('update','restore','checkpoint','init')]
    [string]$Operation,

    [Parameter(Mandatory=$false)]
    [string]$Phase = '',

    [Parameter(Mandatory=$true)]
    [string]$OldStateHash,

    [Parameter(Mandatory=$true)]
    [string]$NewStateHash,

    [Parameter(Mandatory=$true)]
    [ValidateSet('success','failed','rollback')]
    [string]$Status,

    [Parameter(Mandatory=$true)]
    [int]$DurationMs
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Resolve paths from repo root
$repoRoot   = Split-Path $PSScriptRoot -Parent
$journalDir = Join-Path $repoRoot 'data\journal'
$archiveDir = Join-Path $journalDir 'archive'

foreach ($d in @($journalDir, $archiveDir)) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
    }
}

# UTC timestamp with InvariantCulture
$now       = (Get-Date).ToUniversalTime()
$timestamp = $now.ToString('yyyy-MM-ddTHH:mm:ss.fffZ', [System.Globalization.CultureInfo]::InvariantCulture)
$dayStamp  = $now.ToString('yyyyMMdd', [System.Globalization.CultureInfo]::InvariantCulture)

# Build compact JSON line
$entry = [ordered]@{
    timestamp      = $timestamp
    operation      = $Operation
    phase          = $Phase
    old_state_hash = $OldStateHash
    new_state_hash = $NewStateHash
    status         = $Status
    duration_ms    = $DurationMs
}
$jsonLine = $entry | ConvertTo-Json -Depth 10 -Compress

# Daily JSONL file (append)
$journalFile = Join-Path $journalDir "${dayStamp}.jsonl"

# BOM-free UTF-8 with explicit append lock and durable flush
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$bytes = $utf8NoBom.GetBytes($jsonLine + "`n")

$maxAttempts = 10
$delayMs = 50
$lastError = $null

for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
    $stream = $null
    try {
        $stream = [System.IO.FileStream]::new(
            $journalFile,
            [System.IO.FileMode]::Append,
            [System.IO.FileAccess]::Write,
            [System.IO.FileShare]::Read
        )

        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)

        Write-Output "[OK] Journal entry appended: $journalFile"
        return
    } catch {
        $lastError = $_

        if ($attempt -ge $maxAttempts) {
            break
        }

        Start-Sleep -Milliseconds $delayMs
        $delayMs = [Math]::Min($delayMs * 2, 1000)
    } finally {
        if ($null -ne $stream) {
            $stream.Dispose()
        }
    }
}

throw "Failed to write journal entry after $maxAttempts attempts: $lastError"
