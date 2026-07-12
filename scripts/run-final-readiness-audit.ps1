[CmdletBinding()]
param(
    [string]$ExpectedBranch,
    [string]$ExpectedBaseBranch = "main",
    [string]$ReceiptPath = "out/evidence/readiness-audit-receipt.json",
    [string]$DiagnosticPath = "out/evidence/readiness-audit-diagnostic.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:ResolvedExpectedBranch = if (-not [string]::IsNullOrWhiteSpace($ExpectedBranch)) {
    $ExpectedBranch
}
elseif (-not [string]::IsNullOrWhiteSpace($env:EXPECTED_BRANCH)) {
    $env:EXPECTED_BRANCH
}
elseif (-not [string]::IsNullOrWhiteSpace($env:GITHUB_HEAD_REF)) {
    $env:GITHUB_HEAD_REF
}
elseif (-not [string]::IsNullOrWhiteSpace($env:GITHUB_REF_NAME)) {
    $env:GITHUB_REF_NAME
}
else {
    ''
}

$script:ResolvedExpectedBaseBranch = if (-not [string]::IsNullOrWhiteSpace($ExpectedBaseBranch)) {
    $ExpectedBaseBranch
}
else {
    'main'
}

function Write-Utf8NoBomAtomicFile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    $resolvedPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
    $directory = Split-Path -Parent $resolvedPath
    if (-not [string]::IsNullOrWhiteSpace($directory) -and -not (Test-Path -LiteralPath $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }

    $tempPath = "$resolvedPath.tmp"
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($tempPath, $Content, $encoding)

    if (Test-Path -LiteralPath $resolvedPath) {
        Remove-Item -LiteralPath $resolvedPath -Force
    }

    Move-Item -LiteralPath $tempPath -Destination $resolvedPath -Force
}

function Get-GitLines {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $output = & git @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed with exit code $LASTEXITCODE."
    }

    if ($null -eq $output) {
        return @()
    }

    return @($output)
}

function Get-GitText {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $lines = Get-GitLines -Arguments $Arguments
    return ($lines -join "`n").Trim()
}

function Get-GitStatusSnapshot {
    [CmdletBinding()]
    param()

    [pscustomobject]@{
        Branch = Get-GitText -Arguments @('branch', '--show-current')
        Head = Get-GitText -Arguments @('rev-parse', 'HEAD')
        StatusShort = Get-GitLines -Arguments @('status', '--short')
        StatusPorcelain = Get-GitLines -Arguments @('status', '--porcelain=v1')
        DiffNameOnly = Get-GitLines -Arguments @('diff', '--name-only')
        DiffCachedNameOnly = Get-GitLines -Arguments @('diff', '--cached', '--name-only')
    }
}

function Assert-ExpectedBranch {
    [CmdletBinding()]
    param()

    if ([string]::IsNullOrWhiteSpace($script:ResolvedExpectedBranch)) {
        throw 'Expected branch was not provided and could not be resolved from environment.'
    }

    $currentBranch = Get-GitText -Arguments @('branch', '--show-current')
    if ([string]::IsNullOrWhiteSpace($currentBranch)) {
        throw "Expected branch '$script:ResolvedExpectedBranch', but current branch is detached or empty."
    }

    if ($currentBranch -ne $script:ResolvedExpectedBranch) {
        throw "Expected branch '$script:ResolvedExpectedBranch', but current branch is '$currentBranch'."
    }
}

function Assert-CleanWorktree {
    [CmdletBinding()]
    param()

    $status = Get-GitLines -Arguments @('status', '--porcelain=v1')
    if ($status.Count -gt 0) {
        $detail = $status -join ' | '
        throw "Working tree is not clean: $detail"
    }
}

function New-DiagnosticObject {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [bool]$Ok,

        [Parameter(Mandatory = $true)]
        [string]$ErrorMessage
    )

    $snapshot = Get-GitStatusSnapshot
    return [ordered]@{
        ok = $Ok
        expectedBranch = $script:ResolvedExpectedBranch
        expectedBaseBranch = $script:ResolvedExpectedBaseBranch
        currentBranch = $snapshot.Branch
        head = $snapshot.Head
        statusShort = $snapshot.StatusShort
        statusPorcelain = $snapshot.StatusPorcelain
        diffNameOnly = $snapshot.DiffNameOnly
        diffCachedNameOnly = $snapshot.DiffCachedNameOnly
        error = $ErrorMessage
        timestampUtc = (Get-Date).ToUniversalTime().ToString('o')
    }
}

try {
    $repoRoot = Get-GitText -Arguments @('rev-parse', '--show-toplevel')
    if ([string]::IsNullOrWhiteSpace($repoRoot)) {
        throw 'Could not resolve repository root.'
    }

    Set-Location -LiteralPath $repoRoot

    Assert-ExpectedBranch
    Assert-CleanWorktree

    $head = Get-GitText -Arguments @('rev-parse', 'HEAD')

    $receipt = [ordered]@{
        ok = $true
        branch = $script:ResolvedExpectedBranch
        baseBranch = $script:ResolvedExpectedBaseBranch
        head = $head
        timestampUtc = (Get-Date).ToUniversalTime().ToString('o')
    }

    $receiptJson = $receipt | ConvertTo-Json -Depth 8
    Write-Utf8NoBomAtomicFile -Path $ReceiptPath -Content $receiptJson

    $diagnostic = New-DiagnosticObject -Ok $true -ErrorMessage ''
    $diagnostic.receiptPath = $ReceiptPath
    $diagnosticJson = $diagnostic | ConvertTo-Json -Depth 12
    Write-Utf8NoBomAtomicFile -Path $DiagnosticPath -Content $diagnosticJson

    Write-Host 'Final readiness audit passed.'
    exit 0
}
catch {
    $message = $_.Exception.Message

    try {
        $diagnostic = New-DiagnosticObject -Ok $false -ErrorMessage $message
        $diagnosticJson = $diagnostic | ConvertTo-Json -Depth 12
        Write-Utf8NoBomAtomicFile -Path $DiagnosticPath -Content $diagnosticJson
    }
    catch {
        Write-Warning "Failed to write diagnostic file: $($_.Exception.Message)"
    }

    Write-Error $message
    exit 1
}
