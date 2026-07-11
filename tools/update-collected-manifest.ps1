[CmdletBinding()]
param(
    [string]$ProjectRoot = 'G:\s43_work\s43_g11_work'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$InboxRoot = Join-Path $ProjectRoot '_inbox_external_files'
$CollectedDir = Join-Path $InboxRoot 'collected'
$ManifestDir = Join-Path $InboxRoot 'manifest'
$LogDir = Join-Path $InboxRoot 'logs'
$ManifestPath = Join-Path $ManifestDir 'collected-manifest.json'
$LedgerPath = Join-Path $ManifestDir 'collected-import-ledger.jsonl'
$RunLogPath = Join-Path $LogDir ("collected-manifest-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))

$null = New-Item -ItemType Directory -Force -Path $CollectedDir,$ManifestDir,$LogDir

function Write-Log {
    param([string]$Message)
    $Line = "[{0}] {1}" -f (Get-Date).ToString('o'), $Message
    $Line | Tee-Object -FilePath $RunLogPath -Append | Out-Null
}

$LedgerEntries = @()
if (Test-Path -LiteralPath $LedgerPath) {
    $LedgerEntries = Get-Content -LiteralPath $LedgerPath | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json }
}

$Files = Get-ChildItem -LiteralPath $CollectedDir -File -Force | Sort-Object Name

$Items = foreach ($File in $Files) {
    $Hash = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash
    $MatchingLedger = $LedgerEntries | Where-Object { $_.DestinationFullName -eq $File.FullName } | Select-Object -Last 1

    $SourceFullName = $null
    $SourceSHA256 = $null
    $ImportedAt = $null
    $ReviewStatus = 'Unreviewed'

    if ($null -ne $MatchingLedger) {
        if ($MatchingLedger.PSObject.Properties.Name -contains 'SourceFullName') { $SourceFullName = $MatchingLedger.SourceFullName }
        if ($MatchingLedger.PSObject.Properties.Name -contains 'SourceSHA256') { $SourceSHA256 = $MatchingLedger.SourceSHA256 }
        if ($MatchingLedger.PSObject.Properties.Name -contains 'ImportedAt') { $ImportedAt = $MatchingLedger.ImportedAt }
        if (($MatchingLedger.PSObject.Properties.Name -contains 'ReviewStatus') -and $MatchingLedger.ReviewStatus) { $ReviewStatus = $MatchingLedger.ReviewStatus }
    }

    [pscustomobject]@{
        Name                   = $File.Name
        FullName               = $File.FullName
        Length                 = $File.Length
        LastWriteTime          = $File.LastWriteTime
        SHA256                 = $Hash
        SourceFullName         = $SourceFullName
        SourceSHA256           = $SourceSHA256
        ImportedAt             = $ImportedAt
        Policy                 = 'RetainUntilManualReview'
        ReviewStatus           = $ReviewStatus
        Classification         = 'Unclassified'
        RecommendedDisposition = 'Keep'
    }
}

$Manifest = [pscustomobject]@{
    ProjectRoot     = $ProjectRoot
    GeneratedAt     = (Get-Date).ToString('o')
    ManifestVersion = 1
    RetentionPolicy = 'No automatic deletion. Manual review required.'
    ItemCount       = @($Items).Count
    Items           = @($Items)
}

$Manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8
Write-Log "Manifest updated: $ManifestPath"
Write-Output $ManifestPath
