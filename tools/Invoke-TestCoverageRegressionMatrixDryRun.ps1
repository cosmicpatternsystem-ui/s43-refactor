param(
    [string]$AuditPath
)

$ErrorActionPreference = "Stop"

if (-not $AuditPath) {
    throw "AuditPath is required."
}

Write-Host "PHASE24_TEST_COVERAGE_DRY_RUN_START"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$signals = @()

if (Test-Path ".\pytest.ini") { $signals += "pytest.ini" }
if (Test-Path ".\pyproject.toml") { $signals += "pyproject.toml" }
if (Test-Path ".\requirements.txt") { $signals += "requirements.txt" }
if (Test-Path ".\package.json") { $signals += "package.json" }
if (Test-Path ".\tox.ini") { $signals += "tox.ini" }

$testFiles = @()
if (Get-Command rg -ErrorAction SilentlyContinue) {
    $testFiles = rg --files | rg "test|tests|spec"
} else {
    $testFiles = Get-ChildItem -Recurse -File | Where-Object {
        $_.Name -match "test|tests|spec"
    } | ForEach-Object { $_.FullName }
}

Add-Content -Path $AuditPath -Value ""
Add-Content -Path $AuditPath -Value "## Detected Signals"
if ($signals.Count -eq 0) {
    Add-Content -Path $AuditPath -Value "- none detected automatically"
} else {
    $signals | ForEach-Object { Add-Content -Path $AuditPath -Value "- $_" }
}

Add-Content -Path $AuditPath -Value ""
Add-Content -Path $AuditPath -Value "## Detected Test Files"
if (-not $testFiles -or $testFiles.Count -eq 0) {
    Add-Content -Path $AuditPath -Value "- no test-like files detected automatically"
} else {
    $testFiles | Select-Object -First 200 | ForEach-Object {
        Add-Content -Path $AuditPath -Value "- $_"
    }
}

Write-Host "PHASE24_TEST_COVERAGE_DRY_RUN_PASS"
