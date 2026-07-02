<#
.SYNOPSIS
    Write atomic journal entry for roadmap operations
.DESCRIPTION
    Creates immutable journal entries in data/journal/ with timestamp, operation, hashes
    Part of Phase B.2 Durability - 50-year audit trail
.PARAMETER Operation
    Operation type: update, restore, checkpoint
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

# Ensure journal directory exists
$journalDir = 'data/journal'
$archiveDir = 'data/journal/archive'
if (-not (Test-Path $journalDir)) {
    New-Item -ItemType Directory -Path $journalDir -Force | Out-Null
}
if (-not (Test-Path $archiveDir)) {
    New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
}

# Generate timestamp in ISO 8601 format (cp1252-safe)
$timestamp = Get-Date -Format 'yyyy-MM-ddTHH:mm:ss.fffZ'

# Create journal entry
$entry = [ordered]@{
    timestamp = $timestamp
    operation = $Operation
    phase = $Phase
    old_state_hash = $OldStateHash
    new_state_hash = $NewStateHash
    status = $Status
    duration_ms = $DurationMs
}

# Generate journal filename: YYYYMMDD_HHMMSSfff_operation.json
$fileTimestamp = Get-Date -Format 'yyyyMMdd_HHmmssffff'
$journalFile = Join-Path $journalDir "${fileTimestamp}_${Operation}.jsonl"

# Write atomically
$tempFile = "$journalFile.tmp"
try {
    $entry | ConvertTo-Json -Depth 10 -Compress | Set-Content -Path $tempFile -Encoding UTF8 -NoNewline
    Move-Item -Path $tempFile -Destination $journalFile -Force
    Write-Output "[OK] Journal entry written: $journalFile"
} catch {
    if (Test-Path $tempFile) { Remove-Item $tempFile -Force }
    throw "Failed to write journal entry: $_"
}
