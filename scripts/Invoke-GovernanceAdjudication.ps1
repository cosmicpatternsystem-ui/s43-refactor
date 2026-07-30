[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$TaskId,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$WaiverId,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$WaiverExpiry,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ReviewFile,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$SummaryFile,

    [string]$WaiverFile = 'governance/authority_waivers.json',
    [string]$RoadmapFile = 'docs/governance/ROADMAP_CURRENT.json',

    [string]$ExpectedReviewVerdict = 'Authority Not Established',
    [string]$DefaultFinalDisposition = 'Authority Not Established',
    [string]$EstablishedFinalDisposition = 'Authority Established',

    [string]$RepositoryPosture = 'CONTROLLED_BLOCKED',
    [string]$HandlingMode = 'review-only',
    [string]$EnforcementMode = 'fail-closed',

    [switch]$DryRun,
    [switch]$CreateBackup
)

Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'

function Read-Utf8Text {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "File not found: $Path"
    }

    $resolved = Resolve-Path -LiteralPath $Path
    [System.IO.File]::ReadAllText($resolved.Path, [System.Text.Encoding]::UTF8)
}

function Write-Utf8Text {
    param(
        [string]$Path,
        [string]$Text
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $directory = Split-Path -Parent $fullPath

    if ($directory -and (-not (Test-Path -LiteralPath $directory))) {
        [System.IO.Directory]::CreateDirectory($directory) | Out-Null
    }

    [System.IO.File]::WriteAllText($fullPath, $Text, [System.Text.Encoding]::UTF8)
}

function Get-Lines {
    param([string]$Text)
    ($Text -split "`r?`n")
}

function Find-LineNumber {
    param(
        [string[]]$Lines,
        [string]$Pattern
    )

    $index = 0
    foreach ($line in $Lines) {
        $index++
        if ($line -match $Pattern) {
            return $index
        }
    }

    return $null
}

function New-ClaimResult {
    param(
        [string]$Claim,
        [string]$Status,
        [string]$File,
        [string]$Detail,
        [object]$Line
    )

    [PSCustomObject]@{
        Claim  = $Claim
        Status = $Status
        File   = $File
        Line   = $Line
        Detail = $Detail
    }
}

function Get-ClaimStatus {
    param(
        [System.Collections.Generic.List[object]]$Results,
        [string]$Claim
    )

    $item = $Results | Where-Object { $_.Claim -eq $Claim } | Select-Object -First 1
    if ($null -eq $item) {
        return 'NOT ESTABLISHED'
    }

    return [string]$item.Status
}

function Get-ClaimLine {
    param(
        [System.Collections.Generic.List[object]]$Results,
        [string]$Claim
    )

    $item = $Results | Where-Object { $_.Claim -eq $Claim } | Select-Object -First 1
    if ($null -eq $item) {
        return $null
    }

    return $item.Line
}

function Get-LineLabel {
    param([object]$Line)

    if ($null -eq $Line) {
        return 'not found'
    }

    return [string]$Line
}

function Normalize-Newlines {
    param([string]$Text)

    if ($null -eq $Text) {
        return ''
    }

    $normalized = $Text -replace "`r`n", "`n"
    $normalized = $normalized -replace "`r", "`n"
    return $normalized
}

function Test-MarkerPresent {
    param(
        [string]$Content,
        [string]$MarkerStart,
        [string]$MarkerEnd
    )

    $normalized = Normalize-Newlines -Text $Content
    return ($normalized.Contains($MarkerStart) -and $normalized.Contains($MarkerEnd))
}

function Find-ConflictingAdjudicationMarkers {
    param(
        [string]$Content,
        [string]$TaskIdValue,
        [string]$WaiverIdValue,
        [string]$WaiverExpiryValue,
        [string]$ExpectedDisposition
    )

    $matches = [regex]::Matches(
        (Normalize-Newlines -Text $Content),
        '<!-- BEGIN ADJUDICATION:([^\|]+)\|([^\|]+)\|([^\|]+)\|(.+?) -->'
    )

    $conflicts = @()
    foreach ($match in $matches) {
        $task = $match.Groups[1].Value
        $waiver = $match.Groups[2].Value
        $expiry = $match.Groups[3].Value
        $disposition = $match.Groups[4].Value

        if (($task -eq $TaskIdValue) -and
            ($waiver -eq $WaiverIdValue) -and
            ($expiry -eq $WaiverExpiryValue) -and
            ($disposition -ne $ExpectedDisposition)) {
            $conflicts += [PSCustomObject]@{
                TaskId           = $task
                WaiverId         = $waiver
                WaiverExpiry     = $expiry
                FinalDisposition = $disposition
            }
        }
    }

    return $conflicts
}

function New-BackupFile {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Cannot create backup because file does not exist: $Path"
    }

    $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backupPath = "$Path.bak.$timestamp"
    Copy-Item -LiteralPath $Path -Destination $backupPath -Force
    return $backupPath
}

function Append-BlockIfMissing {
    param(
        [string]$Path,
        [string]$Block,
        [string]$MarkerStart,
        [string]$MarkerEnd,
        [switch]$NoWrite
    )

    $existing = Read-Utf8Text -Path $Path
    $normalizedExisting = Normalize-Newlines -Text $existing

    if (Test-MarkerPresent -Content $normalizedExisting -MarkerStart $MarkerStart -MarkerEnd $MarkerEnd) {
        return [PSCustomObject]@{
            Changed = $false
            Reason  = 'MarkerAlreadyPresent'
        }
    }

    $newline = [System.Environment]::NewLine
    $trimmedExisting = $existing.TrimEnd("`r", "`n")
    $combined = $trimmedExisting + $newline + $newline + $Block + $newline

    if ($NoWrite) {
        return [PSCustomObject]@{
            Changed = $false
            Reason  = 'DryRun'
        }
    }

    Write-Utf8Text -Path $Path -Text $combined
    return [PSCustomObject]@{
        Changed = $true
        Reason  = 'Appended'
    }
}

$results = New-Object 'System.Collections.Generic.List[object]'

$waiverText = Read-Utf8Text -Path $WaiverFile
$waiverLines = Get-Lines -Text $waiverText
$waiverIdLine = Find-LineNumber -Lines $waiverLines -Pattern ([regex]::Escape($WaiverId))
$waiverExpiryLine = Find-LineNumber -Lines $waiverLines -Pattern ([regex]::Escape($WaiverExpiry))

if (($null -ne $waiverIdLine) -and ($null -ne $waiverExpiryLine)) {
    $results.Add((New-ClaimResult -Claim 'C1' -Status 'ESTABLISHED' -File $WaiverFile -Detail "Verified waiver id '$WaiverId' and expiry '$WaiverExpiry'." -Line $waiverIdLine))
} else {
    $results.Add((New-ClaimResult -Claim 'C1' -Status 'NOT ESTABLISHED' -File $WaiverFile -Detail "Missing waiver id and/or expiry for '$WaiverId'." -Line $waiverIdLine))
}

$roadmapText = Read-Utf8Text -Path $RoadmapFile
$roadmapLines = Get-Lines -Text $roadmapText
$taskRoadmapLine = Find-LineNumber -Lines $roadmapLines -Pattern ([regex]::Escape($TaskId))

if ($null -ne $taskRoadmapLine) {
    $results.Add((New-ClaimResult -Claim 'C2' -Status 'ESTABLISHED' -File $RoadmapFile -Detail "Task '$TaskId' found in roadmap source-of-truth." -Line $taskRoadmapLine))
} else {
    $results.Add((New-ClaimResult -Claim 'C2' -Status 'NOT FOUND' -File $RoadmapFile -Detail "Task '$TaskId' not found in roadmap source-of-truth; structural binding not established." -Line $null))
}

$reviewText = Read-Utf8Text -Path $ReviewFile
$reviewLines = Get-Lines -Text $reviewText
$reviewTaskLine = Find-LineNumber -Lines $reviewLines -Pattern ([regex]::Escape($TaskId))
$reviewVerdictLine = Find-LineNumber -Lines $reviewLines -Pattern ([regex]::Escape($ExpectedReviewVerdict))

if (($null -ne $reviewTaskLine) -and ($null -ne $reviewVerdictLine)) {
    $results.Add((New-ClaimResult -Claim 'C3' -Status 'ESTABLISHED' -File $ReviewFile -Detail "Review record contains task '$TaskId' and verdict '$ExpectedReviewVerdict'." -Line $reviewTaskLine))
} else {
    $results.Add((New-ClaimResult -Claim 'C3' -Status 'NOT ESTABLISHED' -File $ReviewFile -Detail "Review record is missing task '$TaskId' and/or verdict '$ExpectedReviewVerdict'." -Line $reviewTaskLine))
}

$c1Status = Get-ClaimStatus -Results $results -Claim 'C1'
$c2Status = Get-ClaimStatus -Results $results -Claim 'C2'
$c3Status = Get-ClaimStatus -Results $results -Claim 'C3'

$c1Line = Get-ClaimLine -Results $results -Claim 'C1'
$c2Line = Get-ClaimLine -Results $results -Claim 'C2'
$c3Line = Get-ClaimLine -Results $results -Claim 'C3'

$finalDisposition = $DefaultFinalDisposition
$mutationAuthority = 'Not Established'
$holdRelief = 'Not Established'
$finalStatement = "C1 established, C2 not found, C3 established; therefore final disposition remains $DefaultFinalDisposition, and repository posture remains $RepositoryPosture with $HandlingMode / $EnforcementMode handling."

if (($c1Status -eq 'ESTABLISHED') -and ($c2Status -eq 'ESTABLISHED') -and ($c3Status -eq 'ESTABLISHED')) {
    $finalDisposition = $EstablishedFinalDisposition
    $mutationAuthority = 'Established'
    $holdRelief = 'Conditionally Established'
    $finalStatement = 'C1 established, C2 established, C3 established; therefore authority is established subject to repository controls.'
}

$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$markerKey = "ADJUDICATION:$TaskId|$WaiverId|$WaiverExpiry|$finalDisposition"
$markerStart = "<!-- BEGIN $markerKey -->"
$markerEnd = "<!-- END $markerKey -->"

$conflicts = Find-ConflictingAdjudicationMarkers -Content $reviewText `
    -TaskIdValue $TaskId `
    -WaiverIdValue $WaiverId `
    -WaiverExpiryValue $WaiverExpiry `
    -ExpectedDisposition $finalDisposition

$markdownBlock = @"
$markerStart
## Adjudication Update - $TaskId

- Timestamp: $timestamp
- Task: $TaskId
- Waiver: $WaiverId
- Waiver Expiry: $WaiverExpiry

### Claim Verification
- C1: $c1Status
  - File: $WaiverFile
  - Line: $(Get-LineLabel -Line $c1Line)
  - Detail: Verified waiver identifier and expiry evidence.
- C2: $c2Status
  - File: $RoadmapFile
  - Line: $(Get-LineLabel -Line $c2Line)
  - Detail: Structural roadmap binding for $TaskId was not established in the current source-of-truth.
- C3: $c3Status
  - File: $ReviewFile
  - Line: $(Get-LineLabel -Line $c3Line)
  - Detail: Review record contains task evidence and the conclusion '$ExpectedReviewVerdict'.

### Final Disposition
- Final Disposition: $finalDisposition
- Repository Posture: $RepositoryPosture
- Handling Mode: $HandlingMode
- Enforcement Mode: $EnforcementMode
- Mutation Authority: $mutationAuthority
- Hold Relief: $holdRelief

### Final Statement
$finalStatement
$markerEnd
"@

$backupPath = $null
if ($CreateBackup -and (-not $DryRun)) {
    $backupPath = New-BackupFile -Path $ReviewFile
}

$appendResult = Append-BlockIfMissing -Path $ReviewFile `
    -Block $markdownBlock `
    -MarkerStart $markerStart `
    -MarkerEnd $markerEnd `
    -NoWrite:$DryRun

$jsonSummary = [PSCustomObject]@{
    Timestamp                   = $timestamp
    TaskId                      = $TaskId
    WaiverId                    = $WaiverId
    WaiverExpiry                = $WaiverExpiry
    FinalDisposition            = $finalDisposition
    RepositoryPosture           = $RepositoryPosture
    HandlingMode                = $HandlingMode
    EnforcementMode             = $EnforcementMode
    MutationAuthority           = $mutationAuthority
    HoldRelief                  = $holdRelief
    FinalStatement              = $finalStatement
    DryRun                      = [bool]$DryRun
    CreateBackup                = [bool]$CreateBackup
    BackupPath                  = $backupPath
    ReviewFile                  = $ReviewFile
    SummaryFile                 = $SummaryFile
    WaiverFile                  = $WaiverFile
    RoadmapFile                 = $RoadmapFile
    ExpectedReviewVerdict       = $ExpectedReviewVerdict
    MarkerKey                   = $markerKey
    AppendChanged               = $appendResult.Changed
    AppendReason                = $appendResult.Reason
    ConflictingDispositionCount = @($conflicts).Count
    ConflictingDispositions     = @($conflicts)
    Claims = @(
        [PSCustomObject]@{
            Claim  = 'C1'
            Status = $c1Status
            File   = $WaiverFile
            Line   = (Get-LineLabel -Line $c1Line)
        },
        [PSCustomObject]@{
            Claim  = 'C2'
            Status = $c2Status
            File   = $RoadmapFile
            Line   = (Get-LineLabel -Line $c2Line)
        },
        [PSCustomObject]@{
            Claim  = 'C3'
            Status = $c3Status
            File   = $ReviewFile
            Line   = (Get-LineLabel -Line $c3Line)
        }
    )
}

$jsonText = $jsonSummary | ConvertTo-Json -Depth 6
if (-not $DryRun) {
    Write-Utf8Text -Path $SummaryFile -Text $jsonText
}

$markdownBlock
''
Write-Host "Append result: $($appendResult.Reason)"

if ($CreateBackup) {
    if ($DryRun) {
        Write-Host 'Backup skipped because DryRun is active'
    } elseif ($backupPath) {
        Write-Host "Backup created: $backupPath"
    }
}

if (@($conflicts).Count -gt 0) {
    Write-Warning 'Conflicting adjudication marker(s) found for the same task/waiver/expiry with a different final disposition.'
    $conflicts | ForEach-Object {
        Write-Warning ("Conflict: TaskId={0}, WaiverId={1}, WaiverExpiry={2}, FinalDisposition={3}" -f $_.TaskId, $_.WaiverId, $_.WaiverExpiry, $_.FinalDisposition)
    }
}

''
$jsonText