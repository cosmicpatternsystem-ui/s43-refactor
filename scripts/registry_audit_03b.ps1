<#
.SYNOPSIS
    Patch 03B Registry Audit Control for DELIVERY_EVIDENCE_REGISTRY.md.

.DESCRIPTION
    This script performs a deterministic, fail-closed audit of the Delivery Evidence
    Registry structure used by Patch 03B.

    It validates:
      - Registry title at line 1
      - Markdown table header at line 9
      - Markdown separator at line 10
      - Registry data rows at lines 11-25
      - Registry rule at line 28
      - Expected header width of 11 columns
      - Expected data row count of 15 rows
      - Data row width consistency
      - File Name completeness
      - Duplicate File Name detection

    This control is intentionally structure-bound for Patch 03B. It is not a
    general-purpose Markdown parser. This is by design to preserve deterministic
    execution, low churn, and fail-closed governance behavior.

.VERSION
    03B

.AUTHOR
    ASO-X Operational Intel Runtime / Operator: S.Saead Lajevardy

.GOVERNANCE
    Project: ASO-X
    Posture: CONTROLLED_BLOCKED / review-only / fail-closed
    Principle: No capability expansion without authority gain.
    Control: Registry Audit Report Generator - Patch 03B

.INPUTS
    None by pipeline.

.PARAMETER RegistryPath
    Optional path to DELIVERY_EVIDENCE_REGISTRY.md.
    If omitted, the script checks:
      1. .\03_registry\DELIVERY_EVIDENCE_REGISTRY.md
      2. .\DELIVERY_EVIDENCE_REGISTRY.md

.PARAMETER OutputDirectory
    Directory where REGISTRY_AUDIT_REPORT_03B_yyyyMMdd_HHmmss.md will be written.
    Defaults to current directory.

.OUTPUTS
    Markdown audit report plus console summary.

.EXITCODES
    0 = Audit PASS
    1 = Audit FAIL or controlled execution error

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\registry_audit_03b.ps1

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\registry_audit_03b.ps1 -RegistryPath .\03_registry\DELIVERY_EVIDENCE_REGISTRY.md -OutputDirectory .\audit_reports
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$RegistryPath,

    [Parameter(Mandatory = $false)]
    [string]$OutputDirectory = '.'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$global:LASTEXITCODE = 1

try {
    $ScriptVersion = '03B'
    $Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'

    $ExpectedTitle = '# DELIVERY EVIDENCE REGISTRY'
    $ExpectedHeader = '| File Name | Role | Authority Class | Type | Status | Supersedes | Superseded By | Active/Archived | Owner | Review Basis | Notes |'
    $ExpectedSeparator = '|---|---|---|---|---|---|---|---|---|---|---|'
    $ExpectedRule = 'No new file may be introduced without adding a corresponding registry row.'

    if ([string]::IsNullOrWhiteSpace($RegistryPath)) {
        $CandidatePaths = @(
            '.\03_registry\DELIVERY_EVIDENCE_REGISTRY.md',
            '.\DELIVERY_EVIDENCE_REGISTRY.md'
        )

        foreach ($Candidate in $CandidatePaths) {
            if (Test-Path -LiteralPath $Candidate) {
                $RegistryPath = (Resolve-Path -LiteralPath $Candidate).Path
                break
            }
        }

        if ([string]::IsNullOrWhiteSpace($RegistryPath)) {
            throw "Registry file not found. Checked: $($CandidatePaths -join ', ')"
        }
    }
    else {
        if (-not (Test-Path -LiteralPath $RegistryPath)) {
            throw "Registry file not found: $RegistryPath"
        }

        $RegistryPath = (Resolve-Path -LiteralPath $RegistryPath).Path
    }

    if (-not (Test-Path -LiteralPath $OutputDirectory)) {
        New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
    }

    $OutputDirectory = (Resolve-Path -LiteralPath $OutputDirectory).Path

    $Lines = @(Get-Content -LiteralPath $RegistryPath)

    if (-not $Lines -or $Lines.Count -eq 0) {
        throw "Registry file is empty: $RegistryPath"
    }

    if ($Lines.Count -lt 28) {
        throw "Registry file has insufficient lines. Expected at least 28 lines, found $($Lines.Count)."
    }

    $script:Findings = New-Object System.Collections.Generic.List[object]

    function Add-Finding {
        param(
            [Parameter(Mandatory = $true)]
            [string]$Control,

            [Parameter(Mandatory = $true)]
            [ValidateSet('PASS', 'FAIL')]
            [string]$Status,

            [Parameter(Mandatory = $true)]
            [string]$Detail
        )

        $Finding = [pscustomobject]@{
            Control = $Control
            Status  = $Status
            Detail  = $Detail
        }

        [void]$script:Findings.Add($Finding)
    }

    function Assert-Equal {
        param(
            [Parameter(Mandatory = $true)]
            [string]$Control,

            [Parameter(Mandatory = $false)]
            [AllowNull()]
            [string]$Actual,

            [Parameter(Mandatory = $true)]
            [string]$Expected,

            [Parameter(Mandatory = $true)]
            [string]$SuccessDetail,

            [Parameter(Mandatory = $true)]
            [string]$FailureDetail
        )

        if ($Actual -eq $Expected) {
            Add-Finding -Control $Control -Status 'PASS' -Detail $SuccessDetail
        }
        else {
            Add-Finding -Control $Control -Status 'FAIL' -Detail $FailureDetail
        }
    }

    $TitleLine = ([string]$Lines[0]).Trim()
    $HeaderLine = ([string]$Lines[8]).Trim()
    $SeparatorLine = ([string]$Lines[9]).Trim()
    $RuleLine = ([string]$Lines[27]).Trim()

    Assert-Equal `
        -Control 'Registry title' `
        -Actual $TitleLine `
        -Expected $ExpectedTitle `
        -SuccessDetail 'Line 1 matches expected registry title.' `
        -FailureDetail "Line 1 mismatch. Actual: [$TitleLine]"

    Assert-Equal `
        -Control 'Table header' `
        -Actual $HeaderLine `
        -Expected $ExpectedHeader `
        -SuccessDetail 'Line 9 matches expected table header.' `
        -FailureDetail "Line 9 mismatch. Actual: [$HeaderLine]"

    Assert-Equal `
        -Control 'Table separator' `
        -Actual $SeparatorLine `
        -Expected $ExpectedSeparator `
        -SuccessDetail 'Line 10 matches expected markdown separator.' `
        -FailureDetail "Line 10 mismatch. Actual: [$SeparatorLine]"

    Assert-Equal `
        -Control 'Registry rule' `
        -Actual $RuleLine `
        -Expected $ExpectedRule `
        -SuccessDetail 'Line 28 matches expected registry rule.' `
        -FailureDetail "Line 28 mismatch. Actual: [$RuleLine]"

    $HeaderColumns = @($HeaderLine.Trim('|').Split('|') | ForEach-Object { $_.Trim() })

    if ($HeaderColumns.Count -eq 11) {
        Add-Finding -Control 'Header column count' -Status 'PASS' -Detail 'Header contains 11 columns.'
    }
    else {
        Add-Finding -Control 'Header column count' -Status 'FAIL' -Detail "Header contains $($HeaderColumns.Count) columns; expected 11."
    }

    $DataLines = @()
    for ($Index = 10; $Index -le 24; $Index++) {
        $DataLines += $Lines[$Index]
    }

    if ($DataLines.Count -eq 15) {
        Add-Finding -Control 'Data row count' -Status 'PASS' -Detail 'Detected 15 registry data rows at lines 11-25.'
    }
    else {
        Add-Finding -Control 'Data row count' -Status 'FAIL' -Detail "Detected $($DataLines.Count) data rows; expected 15."
    }

    $ParsedRows = New-Object System.Collections.Generic.List[object]
    $WidthFailures = New-Object System.Collections.Generic.List[string]
    $EmptyNameFailures = New-Object System.Collections.Generic.List[string]

    for ($RowOffset = 0; $RowOffset -lt $DataLines.Count; $RowOffset++) {
        $SourceLineNumber = 11 + $RowOffset
        $RawLine = [string]$DataLines[$RowOffset]
        $TrimmedLine = $RawLine.Trim()

        if ([string]::IsNullOrWhiteSpace($TrimmedLine)) {
            [void]$WidthFailures.Add("Line $SourceLineNumber is empty.")
            continue
        }

        if (-not ($TrimmedLine.StartsWith('|') -and $TrimmedLine.EndsWith('|'))) {
            [void]$WidthFailures.Add("Line $SourceLineNumber is not a pipe-delimited markdown row.")
            continue
        }

        $Cells = @($TrimmedLine.Trim('|').Split('|') | ForEach-Object { $_.Trim() })

        if ($Cells.Count -ne 11) {
            [void]$WidthFailures.Add("Line $SourceLineNumber has $($Cells.Count) columns; expected 11.")
            continue
        }

        $FileName = $Cells[0]

        if ([string]::IsNullOrWhiteSpace($FileName)) {
            [void]$EmptyNameFailures.Add("Line $SourceLineNumber has empty File Name.")
        }

        $RowObject = [pscustomobject]@{
            LineNumber = $SourceLineNumber
            FileName   = $FileName
            Cells      = $Cells
        }

        [void]$ParsedRows.Add($RowObject)
    }

    if ($WidthFailures.Count -eq 0) {
        Add-Finding -Control 'Data row width' -Status 'PASS' -Detail 'All data rows are valid 11-column markdown rows.'
    }
    else {
        Add-Finding -Control 'Data row width' -Status 'FAIL' -Detail ($WidthFailures -join ' ')
    }

    if ($EmptyNameFailures.Count -eq 0) {
        Add-Finding -Control 'File name completeness' -Status 'PASS' -Detail 'No blank File Name values detected.'
    }
    else {
        Add-Finding -Control 'File name completeness' -Status 'FAIL' -Detail ($EmptyNameFailures -join ' ')
    }

    $DuplicateGroups = @(
        $ParsedRows |
        Group-Object -Property FileName |
        Where-Object { $_.Count -gt 1 -and -not [string]::IsNullOrWhiteSpace($_.Name) }
    )

    if ($DuplicateGroups.Count -eq 0) {
        Add-Finding -Control 'Duplicate file names' -Status 'PASS' -Detail 'No duplicate File Name values detected.'
    }
    else {
        $DuplicateDetails = @()

        foreach ($Group in $DuplicateGroups) {
            $LineList = @($Group.Group | ForEach-Object { $_.LineNumber }) -join ', '
            $DuplicateDetails += "[$($Group.Name)] appears $($Group.Count) times at lines $LineList."
        }

        Add-Finding -Control 'Duplicate file names' -Status 'FAIL' -Detail ($DuplicateDetails -join ' ')
    }

    $FailureCount = @($script:Findings | Where-Object { $_.Status -eq 'FAIL' }).Count
    $OverallStatus = if ($FailureCount -eq 0) { 'PASS' } else { 'FAIL' }

    $ReportPath = Join-Path -Path $OutputDirectory -ChildPath ("REGISTRY_AUDIT_REPORT_{0}_{1}.md" -f $ScriptVersion, $Timestamp)

    $ReportLines = New-Object System.Collections.Generic.List[string]

    [void]$ReportLines.Add('# Registry Audit Report')
    [void]$ReportLines.Add('')
    [void]$ReportLines.Add("**Script Version:** $ScriptVersion")
    [void]$ReportLines.Add("**Execution Time:** $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))")
    [void]$ReportLines.Add("**Registry Path:** $RegistryPath")
    [void]$ReportLines.Add("**Overall Status:** $OverallStatus")
    [void]$ReportLines.Add('')
    [void]$ReportLines.Add('| Control | Status | Detail |')
    [void]$ReportLines.Add('|---|---|---|')

    foreach ($Finding in $script:Findings) {
        $SafeControl = ([string]$Finding.Control).Replace('|', '/')
        $SafeStatus = ([string]$Finding.Status).Replace('|', '/')
        $SafeDetail = ([string]$Finding.Detail).Replace('|', '/')

        [void]$ReportLines.Add("| $SafeControl | $SafeStatus | $SafeDetail |")
    }

    [void]$ReportLines.Add('')
    [void]$ReportLines.Add('## Decision')

    if ($OverallStatus -eq 'PASS') {
        [void]$ReportLines.Add('Registry audit passed. Control remains fail-closed and evidence is acceptable for review.')
    }
    else {
        [void]$ReportLines.Add('Registry audit failed. Treat registry state as non-compliant and block downstream promotion until corrected.')
    }

    Set-Content -LiteralPath $ReportPath -Value $ReportLines -Encoding UTF8

    Write-Host ''
    Write-Host '=== REGISTRY AUDIT 03B ==='
    Write-Host "Registry Path : $RegistryPath"
    Write-Host "Report Path   : $ReportPath"
    Write-Host "Overall       : $OverallStatus"
    Write-Host ''

    foreach ($Finding in $script:Findings) {
        Write-Host ("[{0}] {1} - {2}" -f $Finding.Status, $Finding.Control, $Finding.Detail)
    }

    Write-Host ''

    if ($OverallStatus -eq 'PASS') {
        $global:LASTEXITCODE = 0
        exit 0
    }

    $global:LASTEXITCODE = 1
    exit 1
}
catch {
    Write-Host ''
    Write-Host '=== REGISTRY AUDIT 03B ==='
    Write-Host ('[FAIL] Controlled audit error - ' + $_.Exception.Message)
    Write-Host ''

    $global:LASTEXITCODE = 1
    exit 1
}
