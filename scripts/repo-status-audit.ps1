Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "=== $Title ===" -ForegroundColor Cyan
}

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Save-Text {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [AllowNull()][object]$Value
    )
    $text = ($Value | Out-String).TrimEnd()
    Set-Content -Path $Path -Value $text -Encoding UTF8
    return $text
}

function Run-Capture {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )
    Write-Host "[RUN] $Label" -ForegroundColor Yellow
    $result = & $Action 2>&1
    Save-Text -Path $Path -Value $result | Out-Null
    $result
}

function Try-Capture {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )
    try {
        Write-Host "[RUN] $Label" -ForegroundColor Yellow
        $result = & $Action 2>&1
        Save-Text -Path $Path -Value $result | Out-Null
        return $result
    }
    catch {
        $msg = "FAILED: $($_.Exception.Message)"
        Write-Warning "$Label $msg"
        Save-Text -Path $Path -Value $msg | Out-Null
        return $null
    }
}

Require-Command git

$hasGh = $true
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    $hasGh = $false
    Write-Warning "GitHub CLI 'gh' not found. GitHub PR/CI data will be skipped."
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    throw "Not inside a git repository."
}

Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path $repoRoot ".audit/repo-status/$timestamp"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Write-Section "Repository"

Save-Text -Path (Join-Path $outDir "00-repo-root.txt") -Value $repoRoot | Out-Null

Run-Capture "Fetch and prune origin" (Join-Path $outDir "01-fetch-prune.txt") {
    git fetch --prune origin
} | Out-Host

$statusShort = Run-Capture "Git status short branch" (Join-Path $outDir "02-status-short-branch.txt") {
    git status --short --branch
}
$statusPorcelain = Run-Capture "Git status porcelain" (Join-Path $outDir "02-status-porcelain.txt") {
    git status --porcelain
}
$branchName = (git branch --show-current).Trim()

Run-Capture "Latest commit" (Join-Path $outDir "03-log-1.txt") {
    git log -1 --oneline
} | Out-Host

Run-Capture "Remotes" (Join-Path $outDir "04-remote-v.txt") {
    git remote -v
} | Out-Host

Run-Capture "Branches" (Join-Path $outDir "05-branches.txt") {
    git branch --all --verbose --no-abbrev
} | Out-Host

Run-Capture "Recent graph" (Join-Path $outDir "06-graph.txt") {
    git log --oneline --decorate --graph --max-count=15 --all
} | Out-Host

$mainHash = (git rev-parse main).Trim()
$originMainHash = (git rev-parse origin/main).Trim()

Save-Text -Path (Join-Path $outDir "07-main-hashes.txt") -Value @(
    "main=$mainHash"
    "origin/main=$originMainHash"
) | Out-Null

git merge-base --is-ancestor main origin/main
$mainAncestorOrigin = $LASTEXITCODE

git merge-base --is-ancestor origin/main main
$originAncestorMain = $LASTEXITCODE

Save-Text -Path (Join-Path $outDir "08-ancestry.txt") -Value @(
    "main<=origin/main exitcode=$mainAncestorOrigin"
    "origin/main<=main exitcode=$originAncestorMain"
) | Out-Null

$ghRepoRaw = $null
$ghOpenPrsRaw = $null
$ghMergedPrsRaw = $null
$ghClosedPrsRaw = $null
$ghRunsRaw = $null

if ($hasGh) {
    Write-Section "GitHub"

    $ghRepoRaw = Try-Capture "GitHub repo view" (Join-Path $outDir "09-gh-repo-view.json") {
        gh repo view --json nameWithOwner,defaultBranchRef
    }
    if ($ghRepoRaw) { $ghRepoRaw | Out-Host }

    $ghOpenPrsRaw = Try-Capture "Open PRs" (Join-Path $outDir "10-gh-pr-open.txt") {
        gh pr list --state open --limit 50
    }
    if ($ghOpenPrsRaw) { $ghOpenPrsRaw | Out-Host }

    $ghMergedPrsRaw = Try-Capture "Merged PRs" (Join-Path $outDir "11-gh-pr-merged.txt") {
        gh pr list --state merged --limit 10
    }
    if ($ghMergedPrsRaw) { $ghMergedPrsRaw | Out-Host }

    $ghClosedPrsRaw = Try-Capture "Closed PRs" (Join-Path $outDir "12-gh-pr-closed.txt") {
        gh pr list --state closed --limit 10
    }
    if ($ghClosedPrsRaw) { $ghClosedPrsRaw | Out-Host }

    $ghRunsRaw = Try-Capture "Recent workflow runs" (Join-Path $outDir "13-gh-runs.txt") {
        gh run list --limit 20
    }
    if ($ghRunsRaw) { $ghRunsRaw | Out-Host }
}

Write-Section "Summary"

$latestCommit = ((Get-Content (Join-Path $outDir "03-log-1.txt") -Raw).Trim())
$repoSlug = $null
$defaultBranch = $null

if ($hasGh -and $ghRepoRaw) {
    try {
        $repoObj = ($ghRepoRaw | Out-String | ConvertFrom-Json)
        $repoSlug = $repoObj.nameWithOwner
        $defaultBranch = $repoObj.defaultBranchRef.name
    }
    catch {
        $repoSlug = $null
        $defaultBranch = $null
    }
}

$isPorcelainClean = [string]::IsNullOrWhiteSpace(($statusPorcelain | Out-String))
$isTrackingOriginMain = (($statusShort | Out-String) -match "## main\.\.\.origin/main")
$isMainEqualOriginMain = ($mainHash -eq $originMainHash)
$isSymmetricAncestor = ($mainAncestorOrigin -eq 0 -and $originAncestorMain -eq 0)

$openPrText = ""
if ($ghOpenPrsRaw -ne $null) {
    $openPrText = ($ghOpenPrsRaw | Out-String).Trim()
}
$hasOpenPrs = -not [string]::IsNullOrWhiteSpace($openPrText)

$runText = ""
if ($ghRunsRaw -ne $null) {
    $runText = ($ghRunsRaw | Out-String).Trim()
}
$failedRunLines = @()
if (-not [string]::IsNullOrWhiteSpace($runText)) {
    $failedRunLines = @($runText -split "`r?`n" | Where-Object { Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "=== $Title ===" -ForegroundColor Cyan
}

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Save-Text {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [AllowNull()][object]$Value
    )
    $text = ($Value | Out-String).TrimEnd()
    Set-Content -Path $Path -Value $text -Encoding UTF8
    return $text
}

function Run-Capture {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )
    Write-Host "[RUN] $Label" -ForegroundColor Yellow
    $result = & $Action 2>&1
    Save-Text -Path $Path -Value $result | Out-Null
    $result
}

function Try-Capture {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )
    try {
        Write-Host "[RUN] $Label" -ForegroundColor Yellow
        $result = & $Action 2>&1
        Save-Text -Path $Path -Value $result | Out-Null
        return $result
    }
    catch {
        $msg = "FAILED: $($_.Exception.Message)"
        Write-Warning "$Label $msg"
        Save-Text -Path $Path -Value $msg | Out-Null
        return $null
    }
}

Require-Command git

$hasGh = $true
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    $hasGh = $false
    Write-Warning "GitHub CLI 'gh' not found. GitHub PR/CI data will be skipped."
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    throw "Not inside a git repository."
}

Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path $repoRoot ".audit/repo-status/$timestamp"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Write-Section "Repository"

Save-Text -Path (Join-Path $outDir "00-repo-root.txt") -Value $repoRoot | Out-Null

Run-Capture "Fetch and prune origin" (Join-Path $outDir "01-fetch-prune.txt") {
    git fetch --prune origin
} | Out-Host

$statusShort = Run-Capture "Git status short branch" (Join-Path $outDir "02-status-short-branch.txt") {
    git status --short --branch
}
$statusPorcelain = Run-Capture "Git status porcelain" (Join-Path $outDir "02-status-porcelain.txt") {
    git status --porcelain
}
$branchName = (git branch --show-current).Trim()

Run-Capture "Latest commit" (Join-Path $outDir "03-log-1.txt") {
    git log -1 --oneline
} | Out-Host

Run-Capture "Remotes" (Join-Path $outDir "04-remote-v.txt") {
    git remote -v
} | Out-Host

Run-Capture "Branches" (Join-Path $outDir "05-branches.txt") {
    git branch --all --verbose --no-abbrev
} | Out-Host

Run-Capture "Recent graph" (Join-Path $outDir "06-graph.txt") {
    git log --oneline --decorate --graph --max-count=15 --all
} | Out-Host

$mainHash = (git rev-parse main).Trim()
$originMainHash = (git rev-parse origin/main).Trim()

Save-Text -Path (Join-Path $outDir "07-main-hashes.txt") -Value @(
    "main=$mainHash"
    "origin/main=$originMainHash"
) | Out-Null

git merge-base --is-ancestor main origin/main
$mainAncestorOrigin = $LASTEXITCODE

git merge-base --is-ancestor origin/main main
$originAncestorMain = $LASTEXITCODE

Save-Text -Path (Join-Path $outDir "08-ancestry.txt") -Value @(
    "main<=origin/main exitcode=$mainAncestorOrigin"
    "origin/main<=main exitcode=$originAncestorMain"
) | Out-Null

$ghRepoRaw = $null
$ghOpenPrsRaw = $null
$ghMergedPrsRaw = $null
$ghClosedPrsRaw = $null
$ghRunsRaw = $null

if ($hasGh) {
    Write-Section "GitHub"

    $ghRepoRaw = Try-Capture "GitHub repo view" (Join-Path $outDir "09-gh-repo-view.json") {
        gh repo view --json nameWithOwner,defaultBranchRef
    }
    if ($ghRepoRaw) { $ghRepoRaw | Out-Host }

    $ghOpenPrsRaw = Try-Capture "Open PRs" (Join-Path $outDir "10-gh-pr-open.txt") {
        gh pr list --state open --limit 50
    }
    if ($ghOpenPrsRaw) { $ghOpenPrsRaw | Out-Host }

    $ghMergedPrsRaw = Try-Capture "Merged PRs" (Join-Path $outDir "11-gh-pr-merged.txt") {
        gh pr list --state merged --limit 10
    }
    if ($ghMergedPrsRaw) { $ghMergedPrsRaw | Out-Host }

    $ghClosedPrsRaw = Try-Capture "Closed PRs" (Join-Path $outDir "12-gh-pr-closed.txt") {
        gh pr list --state closed --limit 10
    }
    if ($ghClosedPrsRaw) { $ghClosedPrsRaw | Out-Host }

    $ghRunsRaw = Try-Capture "Recent workflow runs" (Join-Path $outDir "13-gh-runs.txt") {
        gh run list --limit 20
    }
    if ($ghRunsRaw) { $ghRunsRaw | Out-Host }
}

Write-Section "Summary"

$latestCommit = ((Get-Content (Join-Path $outDir "03-log-1.txt") -Raw).Trim())
$repoSlug = $null
$defaultBranch = $null

if ($hasGh -and $ghRepoRaw) {
    try {
        $repoObj = ($ghRepoRaw | Out-String | ConvertFrom-Json)
        $repoSlug = $repoObj.nameWithOwner
        $defaultBranch = $repoObj.defaultBranchRef.name
    }
    catch {
        $repoSlug = $null
        $defaultBranch = $null
    }
}

$isPorcelainClean = [string]::IsNullOrWhiteSpace(($statusPorcelain | Out-String))
$isTrackingOriginMain = (($statusShort | Out-String) -match "## main\.\.\.origin/main")
$isMainEqualOriginMain = ($mainHash -eq $originMainHash)
$isSymmetricAncestor = ($mainAncestorOrigin -eq 0 -and $originAncestorMain -eq 0)

$openPrText = ""
if ($ghOpenPrsRaw -ne $null) {
    $openPrText = ($ghOpenPrsRaw | Out-String).Trim()
}
$hasOpenPrs = -not [string]::IsNullOrWhiteSpace($openPrText)

$runText = ""
if ($ghRunsRaw -ne $null) {
    $runText = ($ghRunsRaw | Out-String).Trim()
}
$failedRunLines = @()
if (-not [string]::IsNullOrWhiteSpace($runText)) {
    $failedRunLines = $runText -split "`r?`n" | Where-Object { $_ -match "\bfailure\b" }
}
$hasFailedRuns = ($failedRunLines.Count -gt 0)

$summary = [System.Collections.Generic.List[string]]::new()
$summary.Add("Repository root: $repoRoot")
if ($repoSlug) { $summary.Add("GitHub repository: $repoSlug") }
if ($defaultBranch) { $summary.Add("Default branch: $defaultBranch") }
$summary.Add("Current branch: $branchName")
$summary.Add("Latest commit: $latestCommit")
$summary.Add("main hash: $mainHash")
$summary.Add("origin/main hash: $originMainHash")
$summary.Add("Working tree porcelain clean: $isPorcelainClean")
$summary.Add("Status tracks main...origin/main: $isTrackingOriginMain")
$summary.Add("main equals origin/main: $isMainEqualOriginMain")
$summary.Add("Symmetric ancestry main/origin-main: $isSymmetricAncestor")
if ($hasGh) {
    $summary.Add("Open PRs present: $hasOpenPrs")
    $summary.Add("Recent workflow failures present: $hasFailedRuns")
}
if ($hasFailedRuns) {
    $summary.Add("")
    $summary.Add("Failed workflow lines:")
    foreach ($line in $failedRunLines) {
        $summary.Add($line)
    }
}

$summaryPath = Join-Path $outDir "99-summary.txt"
Save-Text -Path $summaryPath -Value $summary | Out-Null

$report = [System.Collections.Generic.List[string]]::new()
$report.Add("# Repository Status Audit")
$report.Add("")
$report.Add("- Repository root: ``$repoRoot``")
if ($repoSlug) { $report.Add("- GitHub repository: ``$repoSlug``") }
if ($defaultBranch) { $report.Add("- Default branch: ``$defaultBranch``") }
$report.Add("- Current branch: ``$branchName``")
$report.Add("- Latest commit: ``$latestCommit``")
$report.Add("- main hash: ``$mainHash``")
$report.Add("- origin/main hash: ``$originMainHash``")
$report.Add("- Working tree clean: ``$isPorcelainClean``")
$report.Add("- main equals origin/main: ``$isMainEqualOriginMain``")
$report.Add("- Symmetric ancestry: ``$isSymmetricAncestor``")
if ($hasGh) {
    $report.Add("- Open PRs present: ``$hasOpenPrs``")
    $report.Add("- Recent workflow failures present: ``$hasFailedRuns``")
}
if ($hasFailedRuns) {
    $report.Add("")
    $report.Add("## Failed Workflow Lines")
    foreach ($line in $failedRunLines) {
        $report.Add("- ``$line``")
    }
}

$reportPath = Join-Path $outDir "REPORT.md"
Save-Text -Path $reportPath -Value $report | Out-Null

$summary | Out-Host

Write-Host ""
Write-Host "Audit artifacts written to:" -ForegroundColor Green
Write-Host $outDir -ForegroundColor Green
Write-Host ""
Write-Host "Primary summary file:" -ForegroundColor Green
Write-Host $summaryPath -ForegroundColor Green
Write-Host ""
Write-Host "Markdown report:" -ForegroundColor Green
Write-Host $reportPath -ForegroundColor Green

if ($hasFailedRuns) {
    Write-Host ""
    Write-Host "WARNING: Recent workflow failures were detected. Inspect 13-gh-runs.txt or GitHub Actions." -ForegroundColor Red
    exit 2
}

if (-not $isPorcelainClean -or -not $isMainEqualOriginMain -or -not $isSymmetricAncestor) {
    Write-Host ""
    Write-Host "WARNING: Repository is not fully clean/synced." -ForegroundColor Red
    exit 1
}

exit 0
 -match "\bfailure\b" })
}
$hasFailedRuns = ($failedRunLines.Count -gt 0)

$summary = [System.Collections.Generic.List[string]]::new()
$summary.Add("Repository root: $repoRoot")
if ($repoSlug) { $summary.Add("GitHub repository: $repoSlug") }
if ($defaultBranch) { $summary.Add("Default branch: $defaultBranch") }
$summary.Add("Current branch: $branchName")
$summary.Add("Latest commit: $latestCommit")
$summary.Add("main hash: $mainHash")
$summary.Add("origin/main hash: $originMainHash")
$summary.Add("Working tree porcelain clean: $isPorcelainClean")
$summary.Add("Status tracks main...origin/main: $isTrackingOriginMain")
$summary.Add("main equals origin/main: $isMainEqualOriginMain")
$summary.Add("Symmetric ancestry main/origin-main: $isSymmetricAncestor")
if ($hasGh) {
    $summary.Add("Open PRs present: $hasOpenPrs")
    $summary.Add("Recent workflow failures present: $hasFailedRuns")
}
if ($hasFailedRuns) {
    $summary.Add("")
    $summary.Add("Failed workflow lines:")
    foreach ($line in $failedRunLines) {
        $summary.Add($line)
    }
}

$summaryPath = Join-Path $outDir "99-summary.txt"
Save-Text -Path $summaryPath -Value $summary | Out-Null

$report = [System.Collections.Generic.List[string]]::new()
$report.Add("# Repository Status Audit")
$report.Add("")
$report.Add("- Repository root: ``$repoRoot``")
if ($repoSlug) { $report.Add("- GitHub repository: ``$repoSlug``") }
if ($defaultBranch) { $report.Add("- Default branch: ``$defaultBranch``") }
$report.Add("- Current branch: ``$branchName``")
$report.Add("- Latest commit: ``$latestCommit``")
$report.Add("- main hash: ``$mainHash``")
$report.Add("- origin/main hash: ``$originMainHash``")
$report.Add("- Working tree clean: ``$isPorcelainClean``")
$report.Add("- main equals origin/main: ``$isMainEqualOriginMain``")
$report.Add("- Symmetric ancestry: ``$isSymmetricAncestor``")
if ($hasGh) {
    $report.Add("- Open PRs present: ``$hasOpenPrs``")
    $report.Add("- Recent workflow failures present: ``$hasFailedRuns``")
}
if ($hasFailedRuns) {
    $report.Add("")
    $report.Add("## Failed Workflow Lines")
    foreach ($line in $failedRunLines) {
        $report.Add("- ``$line``")
    }
}

$reportPath = Join-Path $outDir "REPORT.md"
Save-Text -Path $reportPath -Value $report | Out-Null

$summary | Out-Host

Write-Host ""
Write-Host "Audit artifacts written to:" -ForegroundColor Green
Write-Host $outDir -ForegroundColor Green
Write-Host ""
Write-Host "Primary summary file:" -ForegroundColor Green
Write-Host $summaryPath -ForegroundColor Green
Write-Host ""
Write-Host "Markdown report:" -ForegroundColor Green
Write-Host $reportPath -ForegroundColor Green

if ($hasFailedRuns) {
    Write-Host ""
    Write-Host "WARNING: Recent workflow failures were detected. Inspect 13-gh-runs.txt or GitHub Actions." -ForegroundColor Red
    exit 2
}

if (-not $isPorcelainClean -or -not $isMainEqualOriginMain -or -not $isSymmetricAncestor) {
    Write-Host ""
    Write-Host "WARNING: Repository is not fully clean/synced." -ForegroundColor Red
    exit 1
}

exit 0

