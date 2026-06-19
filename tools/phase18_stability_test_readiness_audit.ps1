[CmdletBinding()]
param(
    [string]$ExpectedBranch = "phase17-work-from-restore"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $RepoRoot

$CurrentBranch = (git branch --show-current).Trim()
if ($CurrentBranch -ne $ExpectedBranch) {
    throw "Invalid branch: $CurrentBranch"
}

git fetch origin $ExpectedBranch | Out-Null

$Head = (git rev-parse HEAD).Trim()
$Origin = (git rev-parse "origin/$ExpectedBranch").Trim()
if ($Head -ne $Origin) {
    throw "HEAD and origin differ. HEAD=$Head ORIGIN=$Origin"
}

$Status = @(git status --short)
if ($Status.Count -gt 0) {
    throw ("Working tree is not clean before stability audit: " + ($Status -join " | "))
}

$TrackedFiles = @(git ls-files)

$TestRegex = '(^|/)(tests?/.*|test_.*\.py|.*_test\.py|.*\.spec\.(js|ts|tsx)|.*\.test\.(js|ts|tsx))$'
$TestFiles = @($TrackedFiles | Where-Object { $_ -match $TestRegex })

$ConfigCandidates = @(
    "pytest.ini",
    "pyproject.toml",
    "tox.ini",
    "setup.cfg",
    "package.json",
    ".github/workflows",
    ".gitlab-ci.yml"
)

$PresentConfigs = @()
foreach ($Path in $ConfigCandidates) {
    if (Test-Path -LiteralPath $Path) {
        $PresentConfigs += $Path
    }
}

$TopLevelDirs = @()
foreach ($Dir in @("tests", "test", "src", "app", ".github/workflows")) {
    if (Test-Path -LiteralPath $Dir) {
        $TopLevelDirs += $Dir
    }
}

$PytestAvailable = $false
$PytestCollectSucceeded = $false
$PytestCollectOutput = @()
$PytestCollectCount = -1

$pytestCmd = Get-Command pytest -ErrorAction SilentlyContinue
if ($null -ne $pytestCmd) {
    $PytestAvailable = $true
    try {
        $PytestCollectOutput = @(& pytest --collect-only -q 2>&1)
        if ($LASTEXITCODE -eq 0) {
            $PytestCollectSucceeded = $true
            $LastLine = ($PytestCollectOutput | Select-Object -Last 1)
            if ($LastLine -match '([0-9]+)\s+tests?\s+collected') {
                $PytestCollectCount = [int]$matches[1]
            }
        }
    }
    catch {
        $PytestCollectSucceeded = $false
    }
}

$RecentCommits = @(
    git log --oneline -10
)

Write-Host "PHASE18_STABILITY_TEST_AUDIT_COMPLETE"
Write-Host "BRANCH=$CurrentBranch"
Write-Host "HEAD=$Head"
Write-Host "ORIGIN=$Origin"
Write-Host "TRACKED_FILES_TOTAL=$($TrackedFiles.Count)"
Write-Host "TEST_FILES_TOTAL=$($TestFiles.Count)"
Write-Host "CONFIGS_PRESENT=$($PresentConfigs.Count)"
Write-Host "TOP_LEVEL_DIRS_PRESENT=$($TopLevelDirs.Count)"
Write-Host "PYTEST_AVAILABLE=$PytestAvailable"
Write-Host "PYTEST_COLLECT_SUCCEEDED=$PytestCollectSucceeded"
Write-Host "PYTEST_COLLECT_COUNT=$PytestCollectCount"

if ($PresentConfigs.Count -gt 0) {
    Write-Host "CONFIG_LIST_BEGIN"
    foreach ($Item in $PresentConfigs) {
        Write-Host $Item
    }
    Write-Host "CONFIG_LIST_END"
}

if ($TopLevelDirs.Count -gt 0) {
    Write-Host "TOP_LEVEL_DIR_LIST_BEGIN"
    foreach ($Item in $TopLevelDirs) {
        Write-Host $Item
    }
    Write-Host "TOP_LEVEL_DIR_LIST_END"
}

if ($TestFiles.Count -gt 0) {
    Write-Host "TEST_FILE_SAMPLE_BEGIN"
    foreach ($Item in ($TestFiles | Select-Object -First 25)) {
        Write-Host $Item
    }
    Write-Host "TEST_FILE_SAMPLE_END"
}

Write-Host "RECENT_COMMITS_BEGIN"
foreach ($Line in $RecentCommits) {
    Write-Host $Line
}
Write-Host "RECENT_COMMITS_END"

$Readiness = "REVIEW_REQUIRED"
if ($TestFiles.Count -gt 0 -and $PytestAvailable -and $PytestCollectSucceeded) {
    $Readiness = "STABILITY_BASELINE_PRESENT"
}
elseif ($TestFiles.Count -gt 0) {
    $Readiness = "TESTS_PRESENT_BUT_COLLECTION_UNVERIFIED"
}
elseif ($TestFiles.Count -eq 0) {
    $Readiness = "TEST_COVERAGE_RISK"
}

Write-Host "READINESS_CLASSIFICATION=$Readiness"
Write-Host "AUDIT_MODE=READ_ONLY"
