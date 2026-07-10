[CmdletBinding()]
param(
    [string]$WorkDir = 'G:\s43_work\s43_g11_work',
    [string]$RepairPath = 'repair-phase3a-complete.ps1',
    [string]$TargetPath = 'run-phase3a-repair.ps1',
    [string]$EvidenceScript = 'collect-phase3a-evidence.ps1',
    [string]$PromotePath = 'asox-autopilot-phase3a.ps1',
    [switch]$Promote,
    [switch]$ExtractEvidence
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Section {
    param([Parameter(Mandatory)][string]$Text)

    Write-Host ''
    Write-Host "=== $Text ===" -ForegroundColor Cyan
}

function Resolve-InputFile {
    param(
        [Parameter(Mandatory)][string]$BaseDirectory,
        [Parameter(Mandatory)][string]$Path
    )

    $candidate = if ([System.IO.Path]::IsPathRooted($Path)) {
        $Path
    }
    else {
        Join-Path $BaseDirectory $Path
    }

    $fullPath = [System.IO.Path]::GetFullPath($candidate)

    if (-not [System.IO.File]::Exists($fullPath)) {
        throw "Required file was not found: $fullPath"
    }

    return $fullPath
}

function Test-PowerShellSyntax {
    param([Parameter(Mandatory)][string]$Path)

    $tokens = $null
    $parseErrors = $null

    [System.Management.Automation.Language.Parser]::ParseFile(
        $Path,
        [ref]$tokens,
        [ref]$parseErrors
    ) | Out-Null

    if ($parseErrors.Count -gt 0) {
        $details = $parseErrors | ForEach-Object {
            $line = $_.Extent.StartLineNumber
            $column = $_.Extent.StartColumnNumber
            "line ${line}, column ${column}: $($_.Message)"
        }

        throw "Syntax validation failed for '$Path':`n$($details -join "`n")"
    }
}

function Get-EvidenceZipFromOutput {
    param(
        [Parameter(Mandatory)][object[]]$Output,
        [Parameter(Mandatory)][string]$BaseDirectory
    )

    foreach ($entry in $Output) {
        $line = ([string]$entry).Trim().Trim('"').Trim("'")

        if ($line -notmatch '(?i)phase3a_evidence_[^\\/:*?"<>|]+\.zip$') {
            continue
        }

        $candidate = if ([System.IO.Path]::IsPathRooted($line)) {
            $line
        }
        else {
            Join-Path $BaseDirectory $line
        }

        try {
            $candidate = [System.IO.Path]::GetFullPath($candidate)
        }
        catch {
            continue
        }

        if ([System.IO.File]::Exists($candidate)) {
            return $candidate
        }
    }

    return $null
}

function Get-LatestEvidenceZip {
    param([Parameter(Mandatory)][string]$BaseDirectory)

    $files = @(
        [System.IO.Directory]::EnumerateFiles(
            $BaseDirectory,
            'phase3a_evidence_*.zip',
            [System.IO.SearchOption]::TopDirectoryOnly
        )
    )

    if ($files.Count -eq 0) {
        return $null
    }

    return $files |
        ForEach-Object { [System.IO.FileInfo]::new($_) } |
        Sort-Object LastWriteTimeUtc |
        Select-Object -Last 1 -ExpandProperty FullName
}

function Copy-FileAtomically {
    param(
        [Parameter(Mandatory)][string]$SourcePath,
        [Parameter(Mandatory)][string]$DestinationPath
    )

    $destinationDirectory = [System.IO.Path]::GetDirectoryName($DestinationPath)

    if (-not [System.IO.Directory]::Exists($destinationDirectory)) {
        [System.IO.Directory]::CreateDirectory($destinationDirectory) | Out-Null
    }

    $temporaryPath = Join-Path $destinationDirectory (
        '.phase3a-' + [System.Guid]::NewGuid().ToString('N') + '.tmp'
    )

    try {
        [System.IO.File]::Copy($SourcePath, $temporaryPath, $true)

        if ([System.IO.File]::Exists($DestinationPath)) {
            $backupPath = $DestinationPath + '.previous'

            if ([System.IO.File]::Exists($backupPath)) {
                [System.IO.File]::Delete($backupPath)
            }

            [System.IO.File]::Replace(
                $temporaryPath,
                $DestinationPath,
                $backupPath,
                $true
            )
        }
        else {
            [System.IO.File]::Move($temporaryPath, $DestinationPath)
        }
    }
    finally {
        if ([System.IO.File]::Exists($temporaryPath)) {
            [System.IO.File]::Delete($temporaryPath)
        }
    }
}

try {
    $WorkDir = [System.IO.Path]::GetFullPath($WorkDir)

    if (-not [System.IO.Directory]::Exists($WorkDir)) {
        throw "Work directory was not found: $WorkDir"
    }

    Set-Location -LiteralPath $WorkDir

    Write-Section 'Resolving paths'

    $repairFull = Resolve-InputFile -BaseDirectory $WorkDir -Path $RepairPath
    $targetFull = Resolve-InputFile -BaseDirectory $WorkDir -Path $TargetPath
    $evidenceFull = Resolve-InputFile -BaseDirectory $WorkDir -Path $EvidenceScript

    Write-Host "Repair   : $repairFull"
    Write-Host "Target   : $targetFull"
    Write-Host "Evidence : $evidenceFull"

    Write-Section 'Parser validation'

    Test-PowerShellSyntax -Path $repairFull
    Test-PowerShellSyntax -Path $targetFull
    Test-PowerShellSyntax -Path $evidenceFull

    Write-Host 'Syntax validation passed.' -ForegroundColor Green

    Write-Section 'Input hashes'

    $repairHash = (Get-FileHash -LiteralPath $repairFull -Algorithm SHA256).Hash
    $targetHash = (Get-FileHash -LiteralPath $targetFull -Algorithm SHA256).Hash

    Write-Host "Repair SHA256 : $repairHash"
    Write-Host "Target SHA256 : $targetHash"

    Write-Section 'Collecting evidence'

    $startTimeUtc = [DateTime]::UtcNow

    $collectorOutput = @(
        & powershell.exe `
            -NoLogo `
            -NoProfile `
            -NonInteractive `
            -ExecutionPolicy Bypass `
            -File $evidenceFull `
            -RepairPath $repairFull `
            -TargetPath $targetFull 2>&1
    )

    $collectorExitCode = $LASTEXITCODE

    $collectorOutput | ForEach-Object {
        Write-Host ([string]$_)
    }

    if ($collectorExitCode -ne 0) {
        throw "Evidence collector failed with exit code $collectorExitCode."
    }

    $evidenceZip = Get-EvidenceZipFromOutput `
        -Output $collectorOutput `
        -BaseDirectory $WorkDir

    if (-not $evidenceZip) {
        $evidenceZip = Get-LatestEvidenceZip -BaseDirectory $WorkDir
    }

    if (-not $evidenceZip) {
        throw "No evidence zip exists in: $WorkDir"
    }

    $zipInfo = [System.IO.FileInfo]::new($evidenceZip)

    if (-not $zipInfo.Exists) {
        throw "Detected evidence zip does not exist: $evidenceZip"
    }

    if ($zipInfo.Length -le 0) {
        throw "Evidence zip is empty: $evidenceZip"
    }

    Write-Host "Evidence zip : $($zipInfo.FullName)" -ForegroundColor Green
    Write-Host "Zip size     : $($zipInfo.Length) bytes"
    Write-Host "Zip timestamp: $($zipInfo.LastWriteTime)"

    if ($zipInfo.LastWriteTimeUtc -lt $startTimeUtc.AddSeconds(-5)) {
        Write-Warning 'The detected zip may be from an earlier run.'
    }

    $extractDirectory = $null

    if ($ExtractEvidence) {
        Write-Section 'Extracting evidence'

        $extractDirectory = Join-Path $WorkDir (
            [System.IO.Path]::GetFileNameWithoutExtension($zipInfo.Name) +
            '_extracted'
        )

        if ([System.IO.Directory]::Exists($extractDirectory)) {
            [System.IO.Directory]::Delete($extractDirectory, $true)
        }

        Expand-Archive `
            -LiteralPath $zipInfo.FullName `
            -DestinationPath $extractDirectory `
            -Force

        $extractedFiles = @(
            [System.IO.Directory]::EnumerateFiles(
                $extractDirectory,
                '*',
                [System.IO.SearchOption]::AllDirectories
            )
        )

        if ($extractedFiles.Count -eq 0) {
            throw "Evidence archive was extracted but contains no files."
        }

        Write-Host "Evidence dir : $extractDirectory" -ForegroundColor Green
        Write-Host "Extracted    : $($extractedFiles.Count) files"
    }

    $promotedFull = $null

    if ($Promote) {
        Write-Section 'Promoting canonical repair'

        $promotedFull = if ([System.IO.Path]::IsPathRooted($PromotePath)) {
            [System.IO.Path]::GetFullPath($PromotePath)
        }
        else {
            [System.IO.Path]::GetFullPath(
                (Join-Path $WorkDir $PromotePath)
            )
        }

        Copy-FileAtomically `
            -SourcePath $repairFull `
            -DestinationPath $promotedFull

        Test-PowerShellSyntax -Path $promotedFull

        $promotedHash = (
            Get-FileHash -LiteralPath $promotedFull -Algorithm SHA256
        ).Hash

        if ($promotedHash -ne $repairHash) {
            throw 'Promoted file hash does not match the canonical repair hash.'
        }

        Write-Host "Promoted to   : $promotedFull" -ForegroundColor Green
        Write-Host "Promote SHA256: $promotedHash"

        $backupPath = $promotedFull + '.previous'
        if ([System.IO.File]::Exists($backupPath)) {
            Write-Host "Previous copy : $backupPath"
        }
    }

    Write-Section 'Completed'

    Write-Host 'Phase 3A automation completed successfully.' -ForegroundColor Green
    Write-Host "Evidence zip : $($zipInfo.FullName)"

    if ($extractDirectory) {
        Write-Host "Evidence dir : $extractDirectory"
    }

    if ($promotedFull) {
        Write-Host "Canonical    : $promotedFull"
    }

    exit 0
}
catch {
    Write-Host ''
    Write-Host 'PHASE 3A AUTOMATION FAILED' -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

