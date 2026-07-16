Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

function Write-Ok {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    $oldEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = & git @Args 2>&1
        $code = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $oldEap
    }

    $text = ($output | ForEach-Object { $_.ToString() }) -join "`n"
    if ($code -ne 0) {
        throw "git $($Args -join ' ') failed with exit code $code.`n$text"
    }

    return $text.Trim()
}

function Get-Lines {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return @()
    }

    return @(
        $Text -split "`r?`n" |
        Where-Object { $_.Trim() -ne '' }
    )
}

function Test-IsJournalPath {
    param([string]$Path)

    $normalized = $Path.Replace('\', '/')
    return $normalized -like 'data/journal/*'
}

function Test-IsAllowedWorkingTreePath {
    param([string]$Path)

    $normalized = $Path.Replace('\', '/')

    if (Test-IsJournalPath -Path $normalized) {
        return $true
    }

    $allowedWorkingTreePaths = @(
        'scripts/verify-governance-closeout.ps1'
    )

    return $normalized -in $allowedWorkingTreePaths
}

function Get-NonAllowedWorkingTreePaths {
    $status = Invoke-Git @('status', '--short')
    $lines = Get-Lines -Text $status

    $paths = @()
    foreach ($line in $lines) {
        if ($line.Length -lt 4) {
            continue
        }

        $path = $line.Substring(3).Trim()
        if ([string]::IsNullOrWhiteSpace($path)) {
            continue
        }

        $paths += $path
    }

    return @(
        $paths |
        Where-Object { -not (Test-IsAllowedWorkingTreePath -Path $_) } |
        Select-Object -Unique
    )
}

function Get-NonJournalDiffPaths {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Range
    )

    $diff = Invoke-Git @('diff', '--name-only', $Range)
    $paths = Get-Lines -Text $diff

    return @(
        $paths |
        Where-Object { -not (Test-IsJournalPath -Path $_) } |
        Select-Object -Unique
    )
}

function Exit-WithCode {
    param([int]$Code)

    try {
        if ($host -and $host.PSObject.Properties.Name -contains 'SetShouldExit') {
            $host.SetShouldExit($Code)
        }
    }
    catch {
    }

    exit $Code
}

try {
    Write-Host "== Final post-merge governance verification (journal-aware) ==" -ForegroundColor Cyan

    Write-Info "Step 1/7: Verify current branch and fetch remote"
    $branch = Invoke-Git @('branch', '--show-current')
    if ($branch -ne 'main') {
        throw "Expected branch 'main' but found '$branch'."
    }

    Invoke-Git @('fetch', 'origin', 'main') | Out-Null
    Write-Ok "On main and remote fetched."

    Write-Info "Step 2/7: Check working tree (policy: ignore) for journal-only or explicitly allowed changes"
    $nonAllowedWorkingTreePaths = @(Get-NonAllowedWorkingTreePaths)
    if ($nonAllowedWorkingTreePaths.Count -gt 0) {
        $report = $nonAllowedWorkingTreePaths -join "`n"
        throw "Working tree contains non-allowed changes.`n$report"
    }

    $statusShort = Invoke-Git @('status', '--short')
    $statusLines = @(Get-Lines -Text $statusShort)

    if ($statusLines.Count -eq 0) {
        Write-Ok "Working tree clean."
    }
    else {
        Write-Ok "Journal-only changes detected; continuing (ignored for governance)."
    }

    Write-Info "Step 3/7: Verify alignment with origin/main (allow journal-only ahead)"
    $head = Invoke-Git @('rev-parse', 'HEAD')
    $remote = Invoke-Git @('rev-parse', 'origin/main')

    if ($head -ne $remote) {
        $nonJournalAhead = @(Get-NonJournalDiffPaths -Range 'origin/main..HEAD')
        $nonJournalBehind = @(Get-NonJournalDiffPaths -Range 'HEAD..origin/main')
        $nonJournalCombined = @(
            $nonJournalAhead + $nonJournalBehind |
            Where-Object { $_.Trim() -ne '' } |
            Select-Object -Unique
        )

        if ($nonJournalCombined.Count -gt 0) {
            $report = $nonJournalCombined -join "`n"
            throw "main is not aligned with origin/main and differences include non-journal changes.`nHEAD=$head`nREMOTE=$remote`nDIFF:`n$report"
        }

        Write-Ok "Only journal differences detected between local and remote; continuing."
    }
    else {
        Write-Ok "Local main aligned with origin/main."
    }

    Write-Info "Step 4/7: Validate roadmap manifest"
    & pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File 'scripts/validate-roadmap.ps1'
    if ($LASTEXITCODE -ne 0) {
        throw "scripts/validate-roadmap.ps1 failed with exit code $LASTEXITCODE"
    }
    Write-Ok "Roadmap manifest validation passed."

    Write-Info "Step 5/7: Run roadmap tests"
    & pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File 'scripts/test-roadmap.ps1'
    if ($LASTEXITCODE -ne 0) {
        throw "scripts/test-roadmap.ps1 failed with exit code $LASTEXITCODE"
    }
    Write-Ok "Roadmap tests passed."

    Write-Info "Step 6/7: Validate roadmap authority"
    & pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File 'scripts/validate-roadmap-authority.ps1'
    if ($LASTEXITCODE -ne 0) {
        throw "scripts/validate-roadmap-authority.ps1 failed with exit code $LASTEXITCODE"
    }
    Write-Ok "Roadmap authority validation passed."

    Write-Info "Step 7/7: Run governance smoke verification"
    & pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File 'scripts/verify-roadmap-smoke.ps1'
    if ($LASTEXITCODE -ne 0) {
        throw "scripts/verify-roadmap-smoke.ps1 failed with exit code $LASTEXITCODE"
    }
    Write-Ok "Governance smoke verification passed."

    Write-Host ""
    Write-Host "== GOVERNANCE CLOSEOUT VERIFIED ==" -ForegroundColor Green
    Exit-WithCode 0
}
catch {
    Write-Host ""
    Write-Fail "== FAILED =="
    Write-Fail $_.Exception.Message
    Write-Host ""
    Write-Host "Safe diagnostics:" -ForegroundColor Yellow
    Write-Host "  git status --short" -ForegroundColor Yellow
    Write-Host "  git branch --show-current" -ForegroundColor Yellow
    Write-Host "  git rev-parse HEAD" -ForegroundColor Yellow
    Write-Host "  git rev-parse origin/main" -ForegroundColor Yellow
    Write-Host "  git diff --name-only origin/main..HEAD" -ForegroundColor Yellow
    Exit-WithCode 1
}