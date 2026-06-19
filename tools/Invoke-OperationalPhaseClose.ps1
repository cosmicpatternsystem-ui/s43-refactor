param(
    [Parameter(Mandatory = $true)]
    [string]$Phase,

    [Parameter(Mandatory = $true)]
    [string]$Message,

    [string]$AuditPath = "",

    [string]$Remote = "origin",

    [string]$Branch = "",

    [switch]$SkipQualityGate
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host "==> $Name"
    & $Action
}

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed"
    }
}

function Test-CommandExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Repair-TrackedWhitespace {
    $files = @()

    $gitFiles = & git ls-files
    if ($LASTEXITCODE -ne 0) {
        throw "git ls-files failed"
    }

    foreach ($file in $gitFiles) {
        if ($file -match "\.(md|txt|ps1|py|json|yml|yaml)$" -and (Test-Path $file)) {
            $files += $file
        }
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)

    foreach ($file in $files) {
        $fullPath = (Resolve-Path $file).Path
        $content = [System.IO.File]::ReadAllText($fullPath)
        $clean = $content -replace "[ `t]+(`r?`n)", '$1'
        $clean = $clean -replace "[ `t]+$", ""

        if ($clean -ne $content) {
            [System.IO.File]::WriteAllText($fullPath, $clean, $utf8NoBom)
        }
    }
}

if (-not (Test-Path ".git")) {
    throw "Run from repository root."
}

if ([string]::IsNullOrWhiteSpace($Branch)) {
    $Branch = (& git branch --show-current).Trim()
    if ([string]::IsNullOrWhiteSpace($Branch)) {
        throw "Could not detect current branch."
    }
}

if (-not [string]::IsNullOrWhiteSpace($AuditPath)) {
    if (-not (Test-Path $AuditPath)) {
        throw "Audit artifact not found: $AuditPath"
    }
}

Invoke-Step "preflight: git repository status" {
    Invoke-Git @("rev-parse", "--is-inside-work-tree")
    Invoke-Git @("status", "--short")
}

Invoke-Step "repair trailing whitespace before gates" {
    Repair-TrackedWhitespace
}

if (-not $SkipQualityGate) {
    Invoke-Step "quality gate" {
        if (Test-Path "tools/Invoke-QualityGate.ps1") {
            & powershell -NoProfile -ExecutionPolicy Bypass -File "tools/Invoke-QualityGate.ps1"
            if ($LASTEXITCODE -ne 0) {
                throw "tools/Invoke-QualityGate.ps1 failed"
            }
        }
        elseif (Test-Path "scripts/Invoke-QualityGate.ps1") {
            & powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/Invoke-QualityGate.ps1"
            if ($LASTEXITCODE -ne 0) {
                throw "scripts/Invoke-QualityGate.ps1 failed"
            }
        }
        elseif (Test-CommandExists "pytest") {
            & pytest
            if ($LASTEXITCODE -ne 0) {
                throw "pytest failed"
            }
        }
        elseif (Test-CommandExists "python") {
            & python -m pytest
            if ($LASTEXITCODE -ne 0) {
                throw "python -m pytest failed"
            }
        }
        else {
            throw "No quality gate found. Add tools/Invoke-QualityGate.ps1, scripts/Invoke-QualityGate.ps1, or pytest."
        }
    }
}
else {
    Write-Host "WARNING: quality gate skipped by explicit request."
}

Invoke-Step "stage changes" {
    Invoke-Git @("add", "-A")
}

$stagedDiff = @(& git diff --cached --name-only)
if ($LASTEXITCODE -ne 0) {
    throw "git diff --cached --name-only failed"
}

if ($stagedDiff.Count -eq 0) {
    Write-Host "No staged changes found. Continuing to push and sync verification."
}
else {
    Invoke-Step "commit changes" {
        Invoke-Git @("commit", "-m", $Message)
    }
}

Invoke-Step "push branch" {
    Invoke-Git @("push", $Remote, $Branch)
}

Invoke-Step "verify remote sync" {
    Invoke-Git @("fetch", $Remote, $Branch)

    $status = @(& git status --porcelain=v1 -b)
    if ($LASTEXITCODE -ne 0) {
        throw "git status --porcelain=v1 -b failed"
    }

    $statusText = ($status -join "`n")
    Write-Host $statusText

    if ($statusText -match "ahead|behind") {
        throw "Branch is not synchronized with $Remote/$Branch."
    }

    $dirtyLines = @($status | Where-Object { $_ -notmatch "^## " })
    if ($dirtyLines.Count -gt 0) {
        throw "Working tree is not clean after closure."
    }
}

Write-Host ""
Write-Host "OPERATIONAL_PHASE_CLOSE_PASS"
Write-Host "Phase: $Phase"
Write-Host "Branch: $Branch"
Write-Host "Remote: $Remote"
Write-Host "Definition of Done: quality gate -> audit -> commit -> push -> sync verification -> clean worktree"