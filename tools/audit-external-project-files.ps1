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
    [switch]$IncludeHashes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$InboxRoot = Join-Path $ProjectRoot '_inbox_external_files'
$ReportDir = Join-Path $InboxRoot 'reports'
$ManifestDir = Join-Path $InboxRoot 'manifest'
$LogDir = Join-Path $InboxRoot 'logs'

$null = New-Item -ItemType Directory -Force -Path $ReportDir,$ManifestDir,$LogDir

$Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$CsvPath = Join-Path $ReportDir "external-files-candidates-$Timestamp.csv"
$JsonPath = Join-Path $ManifestDir "external-files-audit-$Timestamp.json"
$LogPath = Join-Path $LogDir "external-files-audit-$Timestamp.log"

function Write-Log {
    param([string]$Message)
    $Line = "[{0}] {1}" -f (Get-Date).ToString('o'), $Message
    $Line | Tee-Object -FilePath $LogPath -Append | Out-Null
}

Write-Log "Audit started. ProjectRoot=$ProjectRoot"

$Rows = New-Object System.Collections.Generic.List[object]
$Seen = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)

foreach ($Root in $Roots) {
    if ([string]::IsNullOrWhiteSpace($Root)) { continue }
    if (-not (Test-Path -LiteralPath $Root)) {
        Write-Log "Skipping missing root: $Root"
        continue
    }

    Write-Log "Scanning root: $Root"

    foreach ($Pattern in $Patterns) {
        Get-ChildItem -LiteralPath $Root -Recurse -Force -File -Filter $Pattern -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notlike "$ProjectRoot*" } |
            ForEach-Object {
                if (-not $Seen.Add($_.FullName)) { return }

                $Hash = $null
                if ($IncludeHashes) {
                    try {
                        $Hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
                    }
                    catch {
                        Write-Log "Hash failed for: $($_.FullName) :: $($_.Exception.Message)"
                    }
                }

                $Rows.Add([pscustomobject]@{
                    FullName      = $_.FullName
                    Name          = $_.Name
                    DirectoryName = $_.DirectoryName
                    Length        = $_.Length
                    LastWriteTime = $_.LastWriteTime
                    SHA256        = $Hash
                    ScanTimestamp = (Get-Date).ToString('o')
                    Status        = 'PresentOutsideProject'
                    ProjectRoot   = $ProjectRoot
                }) | Out-Null
            }
    }
}

$SortedRows = $Rows | Sort-Object FullName
$SortedRows | Export-Csv -LiteralPath $CsvPath -NoTypeInformation -Encoding UTF8
[pscustomobject]@{
    GeneratedAt    = (Get-Date).ToString('o')
    ProjectRoot    = $ProjectRoot
    Roots          = $Roots
    Patterns       = $Patterns
    IncludeHashes  = [bool]$IncludeHashes
    CandidateCount = @($SortedRows).Count
    Items          = @($SortedRows)
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $JsonPath -Encoding UTF8

Write-Log "Audit completed. Count=$(@($SortedRows).Count)"
Write-Output $CsvPath
