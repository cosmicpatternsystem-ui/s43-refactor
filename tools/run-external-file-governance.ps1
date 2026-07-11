[CmdletBinding()]
param(
    [string]$ProjectRoot = 'G:\s43_work\s43_g11_work',
    [string[]]$Roots = @(
        [Environment]::GetFolderPath('Desktop'),
        [Environment]::GetFolderPath('MyDocuments'),
        (Join-Path $env:USERPROFILE 'Downloads')
    ),
    [string[]]$Patterns = @(
        '*s43*',
        '*aso*',
        '*asox*',
        '*phase3a*',
        '*autopilot*',
        '*repair*'
    ),
    [switch]$SkipImport,
    [switch]$SkipHashes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$InboxRoot = Join-Path $ProjectRoot '_inbox_external_files'
$ReportDir = Join-Path $InboxRoot 'reports'
$LogDir = Join-Path $InboxRoot 'logs'
$RunLogPath = Join-Path $LogDir ("governance-run-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))

$null = New-Item -ItemType Directory -Force -Path $LogDir

function Write-Log {
    param([string]$Message)
    $Line = "[{0}] {1}" -f (Get-Date).ToString('o'), $Message
    $Line | Tee-Object -FilePath $RunLogPath -Append | Out-Null
}

function Get-LatestAuditCsv {
    param([string]$DirectoryPath)
    Get-ChildItem -LiteralPath $DirectoryPath -Filter 'external-files-candidates-*.csv' -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}

$auditScript = Join-Path $ProjectRoot 'tools\audit-external-project-files.ps1'
$importScript = Join-Path $ProjectRoot 'tools\import-external-file.ps1'
$manifestScript = Join-Path $ProjectRoot 'tools\update-collected-manifest.ps1'

if (-not (Test-Path -LiteralPath $auditScript)) { throw "Missing script: $auditScript" }
if (-not (Test-Path -LiteralPath $importScript)) { throw "Missing script: $importScript" }
if (-not (Test-Path -LiteralPath $manifestScript)) { throw "Missing script: $manifestScript" }

Write-Log "Governance run started"

$auditParams = @{
    ProjectRoot = $ProjectRoot
    Roots       = $Roots
    Patterns    = $Patterns
}
if (-not $SkipHashes) {
    $auditParams.IncludeHashes = $true
}

$AuditCsvPath = & $auditScript @auditParams
Write-Log "AuditCsv=$AuditCsvPath"

$LatestAudit = Get-LatestAuditCsv -DirectoryPath $ReportDir
if (-not $LatestAudit) {
    throw "No audit CSV found in $ReportDir"
}

if (-not $SkipImport) {
    & $importScript -ProjectRoot $ProjectRoot -ReportCsv $LatestAudit.FullName
    Write-Log "Import completed"
}
else {
    Write-Log "Import skipped"
}

$ManifestPath = & $manifestScript -ProjectRoot $ProjectRoot
Write-Log "ManifestPath=$ManifestPath"
Write-Log "Governance run completed"

Write-Output "OK"
