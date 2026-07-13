if (-not $PSVersionTable.PSEdition -or $PSVersionTable.PSEdition -ne 'Core') {
    throw 'This script must be run with PowerShell Core (pwsh).'
}
#Requires -Version 5.1
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
function Invoke-SafeAtomicReplace {
    param(
        [Parameter(Mandatory)][string]$SourcePath,
        [Parameter(Mandatory)][string]$DestinationPath,
        [string]$BackupPath
    )

    $sourceFull = [System.IO.Path]::GetFullPath($SourcePath)
    $destinationFull = [System.IO.Path]::GetFullPath($DestinationPath)
    $destinationDir = [System.IO.Path]::GetDirectoryName($destinationFull)

    if ([string]::IsNullOrWhiteSpace($destinationDir)) {
        throw "Destination directory could not be resolved: $DestinationPath"
    }

    if (-not (Test-Path -LiteralPath $destinationDir -PathType Container)) {
        [System.IO.Directory]::CreateDirectory($destinationDir) | Out-Null
    }

    if (Test-Path -LiteralPath $destinationFull -PathType Leaf) {
        try {
            [System.IO.File]::Replace($sourceFull, $destinationFull, $BackupPath, $true)
            return
        }
        catch {
            if (-not [string]::IsNullOrWhiteSpace($BackupPath)) {
                $backupFull = [System.IO.Path]::GetFullPath($BackupPath)
                $backupDir = [System.IO.Path]::GetDirectoryName($backupFull)
                if (-not [string]::IsNullOrWhiteSpace($backupDir) -and -not (Test-Path -LiteralPath $backupDir -PathType Container)) {
                    [System.IO.Directory]::CreateDirectory($backupDir) | Out-Null
                }
                [System.IO.File]::Copy($destinationFull, $backupFull, $true)
            }

            if (Test-Path -LiteralPath $destinationFull -PathType Leaf) {
                Remove-Item -LiteralPath $destinationFull -Force
            }

            Move-Item -LiteralPath $sourceFull -Destination $destinationFull -Force
            return
        }
    }

    Move-Item -LiteralPath $sourceFull -Destination $destinationFull -Force
}
$ErrorActionPreference = 'Stop'

$Repo = 'G:\s43_work\s43_g11_work'
$Repair = Join-Path $Repo 'repair-phase3a-complete.ps1'
$Source = Join-Path $Repo 'asox-autopilot-phase3a-incomplete.txt'
$Output = Join-Path $Repo 'asox-autopilot-phase3a.audit-only.ps1'
$Sidecar = $Output + '.sha256'
$TempOutput = $Output + '.tmp'
$Lock = $Output + '.lock'

$TrustedSourceSha256 =
    '75E922D109CE085078921DAE9F609DB9309E69D3F981AE042AE79ACFCE4D4434'

$Utf8Strict = New-Object System.Text.UTF8Encoding($false, $true)
$Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'

function Write-Step {
    param([string]$Message)
    Write-Host ('[PHASE3A] ' + $Message) -ForegroundColor Cyan
}

function Get-Sha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Assert-PowerShellSyntax {
    param([string]$Path)

    $Tokens = $null
    $Errors = $null

    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $Path,
        [ref]$Tokens,
        [ref]$Errors
    )

    if (@($Errors).Count -gt 0) {
        $Summary = (
            @($Errors) |
                ForEach-Object {
                    '{0} at line {1}: {2}' -f
                        $_.ErrorId,
                        $_.Extent.StartLineNumber,
                        $_.Message
                }
        ) -join ' | '

        throw "Parser validation failed for '$Path': $Summary"
    }
}

function Assert-Utf8NoBomLf {
    param([string]$Path)

    $Bytes = [IO.File]::ReadAllBytes($Path)

    if (
        $Bytes.Length -ge 3 -and
        $Bytes[0] -eq 0xEF -and
        $Bytes[1] -eq 0xBB -and
        $Bytes[2] -eq 0xBF
    ) {
        throw "UTF-8 BOM detected: $Path"
    }

    if ($Bytes -contains 0x0D) {
        throw "CR or CRLF detected: $Path"
    }

    try {
        [void]$Utf8Strict.GetString($Bytes)
    }
    catch {
        throw "Invalid strict UTF-8 in '$Path': $($_.Exception.Message)"
    }
}

$PatchTemp = $null
$OriginalLocation = Get-Location

try {
    Write-Step 'Starting recovery and repair.'

    if (-not (Test-Path -LiteralPath $Repo -PathType Container)) {
        throw "Repository not found: $Repo"
    }

    if (-not (Test-Path -LiteralPath $Repair -PathType Leaf)) {
        throw "Repair script not found: $Repair"
    }

    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        throw "Source file not found: $Source"
    }

    $SourceHash = Get-Sha256 -Path $Source

    if ($SourceHash -ne $TrustedSourceSha256) {
        throw (
            "Source SHA256 mismatch. Expected=$TrustedSourceSha256; " +
            "Actual=$SourceHash"
        )
    }

    Write-Step "Source SHA256 verified: $SourceHash"

    $RepairText = [IO.File]::ReadAllText($Repair, $Utf8Strict)
    $RepairText = $RepairText.Replace("`r`n", "`n").Replace("`r", "`n")

    $OriginalFilter =
        '$_.ErrorId -ne ''MissingEndCurlyBrace'''

    $MissingCatchFilter =
        '$_.ErrorId -ne ''MissingCatchOrFinally'''

    $PatchedFilter = (
        '$_.ErrorId -ne ''MissingEndCurlyBrace'' -and' +
        "`n                    " +
        '$_.ErrorId -ne ''MissingCatchOrFinally'''
    )

    if (-not $RepairText.Contains($MissingCatchFilter)) {
        $FilterCount = (
            [regex]::Matches(
                $RepairText,
                [regex]::Escape($OriginalFilter)
            )
        ).Count

        if ($FilterCount -ne 1) {
            throw (
                "Expected exactly one parser-filter anchor; " +
                "found $FilterCount"
            )
        }

        $RepairText = $RepairText.Replace(
            $OriginalFilter,
            $PatchedFilter
        )

        Write-Step 'Parser filter patched.'
    }
    else {
        Write-Step 'Parser filter is already patched.'
    }

    $HashPattern = (
        '(?m)^(\s*\$ExpectedSourceSha256\s*=\s*'')' +
        '[0-9A-Fa-f]{64}' +
        '(''\s*)$'
    )

    $HashMatches = [regex]::Matches($RepairText, $HashPattern)

    if ($HashMatches.Count -ne 1) {
        throw (
            "Expected exactly one embedded source-hash assignment; " +
            "found $($HashMatches.Count)"
        )
    }

    $HashEvaluator = [System.Text.RegularExpressions.MatchEvaluator]{
        param([System.Text.RegularExpressions.Match]$Match)

        return (
            $Match.Groups[1].Value +
            $TrustedSourceSha256 +
            $Match.Groups[2].Value
        )
    }

    $RepairText = [regex]::Replace(
        $RepairText,
        $HashPattern,
        $HashEvaluator,
        [System.Text.RegularExpressions.RegexOptions]::Multiline
    )

    Write-Step 'Embedded source SHA256 synchronized.'

    $PatchTemp = (
        $Repair +
        '.patch-' +
        [Guid]::NewGuid().ToString('N') +
        '.tmp'
    )

    [IO.File]::WriteAllText(
        $PatchTemp,
        $RepairText,
        $Utf8Strict
    )

    Assert-PowerShellSyntax -Path $PatchTemp
    Assert-Utf8NoBomLf -Path $PatchTemp

    $ReplaceBackup = (
        $Repair +
        '.pre-replace.' +
        $Timestamp +
        '.bak'
    )

    # Atomic replacement with a real backup path.
    [IO.File]::Replace(
        $PatchTemp,
        $Repair,
        $ReplaceBackup
    )

    $PatchTemp = $null

    Write-Step "Repair script replaced atomically."
    Write-Step "Backup: $ReplaceBackup"

    Assert-PowerShellSyntax -Path $Repair
    Assert-Utf8NoBomLf -Path $Repair

    $RepairHash = Get-Sha256 -Path $Repair
    Write-Step "Patched repair SHA256: $RepairHash"

    if (Test-Path -LiteralPath $Lock -PathType Leaf) {
        throw (
            "Lock file exists; concurrent execution refused: $Lock"
        )
    }

    if (Test-Path -LiteralPath $TempOutput -PathType Leaf) {
        $StalePath = $TempOutput + '.stale.' + $Timestamp
        Move-Item -LiteralPath $TempOutput -Destination $StalePath
        Write-Step "Stale temporary output archived: $StalePath"
    }

    foreach ($Artifact in @($Output, $Sidecar)) {
        if (Test-Path -LiteralPath $Artifact -PathType Leaf) {
            $Archive = $Artifact + '.previous.' + $Timestamp
            Move-Item -LiteralPath $Artifact -Destination $Archive
            Write-Step "Previous artifact archived: $Archive"
        }
    }

    Set-Location -LiteralPath $Repo

    Write-Step 'Executing repair script.'

    & powershell.exe `
        -NoLogo `
        -NoProfile `
        -NonInteractive `
        -ExecutionPolicy Bypass `
        -File $Repair

    $ExitCode = $LASTEXITCODE

    if ($ExitCode -ne 0) {
        throw "Repair script exited with code $ExitCode"
    }

    if (-not (Test-Path -LiteralPath $Output -PathType Leaf)) {
        throw "Expected output was not generated: $Output"
    }

    if (-not (Test-Path -LiteralPath $Sidecar -PathType Leaf)) {
        throw "SHA256 sidecar was not generated: $Sidecar"
    }

    Assert-PowerShellSyntax -Path $Output
    Assert-Utf8NoBomLf -Path $Output

    $ActualOutputHash = Get-Sha256 -Path $Output
    $RecordedOutputHash = (
        [IO.File]::ReadAllText($Sidecar, $Utf8Strict)
    ).Trim().ToUpperInvariant()

    if ($RecordedOutputHash -ne $ActualOutputHash) {
        throw (
            "Output sidecar mismatch. " +
            "Recorded=$RecordedOutputHash; Actual=$ActualOutputHash"
        )
    }

    Write-Host ''
    Write-Host '[SUCCESS] Phase 3A repair completed.' `
        -ForegroundColor Green
    Write-Host "Output : $Output" -ForegroundColor Green
    Write-Host "SHA256 : $ActualOutputHash" -ForegroundColor Green
    Write-Host 'Format : UTF-8 without BOM, LF-only' `
        -ForegroundColor Green
    Write-Host 'Parser : valid PowerShell syntax' `
        -ForegroundColor Green
}
catch {
    Write-Host ''
    Write-Error $_.Exception.Message
    exit 1
}
finally {
    if (
        $null -ne $PatchTemp -and
        (Test-Path -LiteralPath $PatchTemp -PathType Leaf)
    ) {
        Remove-Item `
            -LiteralPath $PatchTemp `
            -Force `
            -ErrorAction SilentlyContinue
    }

    Set-Location `
        -LiteralPath $OriginalLocation `
        -ErrorAction SilentlyContinue
}