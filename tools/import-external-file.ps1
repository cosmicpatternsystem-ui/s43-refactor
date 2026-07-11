[CmdletBinding(DefaultParameterSetName = 'ByCsv')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'ByPath')]
    [string[]]$SourcePath,

    [Parameter(Mandatory = $true, ParameterSetName = 'ByCsv')]
    [string]$ReportCsv,

    [string]$ProjectRoot = 'G:\s43_work\s43_g11_work',
    [switch]$SkipHash,
    [switch]$WhatIfOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$InboxRoot = Join-Path $ProjectRoot '_inbox_external_files'
$CollectedDir = Join-Path $InboxRoot 'collected'
$ManifestDir = Join-Path $InboxRoot 'manifest'
$LogDir = Join-Path $InboxRoot 'logs'
$LedgerPath = Join-Path $ManifestDir 'collected-import-ledger.jsonl'
$RunLogPath = Join-Path $LogDir ("external-file-import-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))

$null = New-Item -ItemType Directory -Force -Path $CollectedDir,$ManifestDir,$LogDir

function Write-Log {
    param([string]$Message)
    $Line = "[{0}] {1}" -f (Get-Date).ToString('o'), $Message
    $Line | Tee-Object -FilePath $RunLogPath -Append | Out-Null
}

function New-SafeLeafName {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    $Trimmed = $LiteralPath -replace '^[A-Za-z]:\\', ''
    $Safe = $Trimmed -replace '[\\/:*?"<>|]', '_'
    return $Safe
}

function Add-LedgerEntry {
    param([Parameter(Mandatory = $true)][pscustomobject]$Entry)
    $Entry | ConvertTo-Json -Depth 6 -Compress | Add-Content -LiteralPath $LedgerPath -Encoding UTF8
}

if ($PSCmdlet.ParameterSetName -eq 'ByCsv') {
    if (-not (Test-Path -LiteralPath $ReportCsv)) {
        throw "ReportCsv not found: $ReportCsv"
    }
    $SourcePath = Import-Csv -LiteralPath $ReportCsv | ForEach-Object { $_.FullName }
}

foreach ($Source in $SourcePath) {
    if ([string]::IsNullOrWhiteSpace($Source)) { continue }

    if (-not (Test-Path -LiteralPath $Source)) {
        Write-Log "Missing source: $Source"
        continue
    }

    $Item = Get-Item -LiteralPath $Source
    if ($Item.PSIsContainer) {
        Write-Log "Skipping directory: $Source"
        continue
    }

    $SafeName = New-SafeLeafName -LiteralPath $Item.FullName
    $Dest = Join-Path $CollectedDir $SafeName

    $SourceHash = $null
    $DestHash = $null
    $CopyRequired = $true
    $CopyOutcome = 'Pending'

    if (-not $SkipHash) {
        $SourceHash = (Get-FileHash -LiteralPath $Item.FullName -Algorithm SHA256).Hash
    }

    if (Test-Path -LiteralPath $Dest) {
        if (-not $SkipHash) {
            $DestHash = (Get-FileHash -LiteralPath $Dest -Algorithm SHA256).Hash
            if ($DestHash -eq $SourceHash) {
                $CopyRequired = $false
                $CopyOutcome = 'AlreadyPresentSameHash'
            }
            else {
                $Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
                $Base = [IO.Path]::GetFileNameWithoutExtension($SafeName)
                $Ext = [IO.Path]::GetExtension($SafeName)
                $Dest = Join-Path $CollectedDir ("{0}__{1}{2}" -f $Base, $Stamp, $Ext)
                $CopyOutcome = 'NewVersionCopied'
            }
        }
        else {
            $CopyRequired = $false
            $CopyOutcome = 'AlreadyPresentSkipHash'
        }
    }
    else {
        $CopyOutcome = 'NewCopyRequired'
    }

    if ($WhatIfOnly) {
        Write-Log "WhatIf Source=$($Item.FullName)"
        Write-Log "WhatIf Dest=$Dest"
        Write-Log "WhatIf CopyRequired=$CopyRequired"
    }
    else {
        if ($CopyRequired) {
            Copy-Item -LiteralPath $Item.FullName -Destination $Dest -Force
            if (-not $SkipHash) {
                $DestHash = (Get-FileHash -LiteralPath $Dest -Algorithm SHA256).Hash
            }
            if ($CopyOutcome -eq 'NewCopyRequired') {
                $CopyOutcome = 'Copied'
            }
        }
    }

    $Entry = [pscustomobject]@{
        ImportedAt          = (Get-Date).ToString('o')
        SourceFullName      = $Item.FullName
        SourceName          = $Item.Name
        SourceLength        = $Item.Length
        SourceLastWriteTime = $Item.LastWriteTime
        SourceSHA256        = $SourceHash
        DestinationFullName = $Dest
        DestinationName     = [IO.Path]::GetFileName($Dest)
        DestinationSHA256   = $DestHash
        CopyRequired        = $CopyRequired
        CopyOutcome         = $CopyOutcome
        ProjectRoot         = $ProjectRoot
        Policy              = 'CopyOnly-NoDelete-NoMove'
        ReviewStatus        = 'Unreviewed'
    }

    if (-not $WhatIfOnly) {
        Add-LedgerEntry -Entry $Entry
    }

    Write-Log "Processed: $($Item.FullName) => $Dest :: $CopyOutcome"
}
