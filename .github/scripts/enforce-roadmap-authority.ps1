[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path $RepoRoot).Path
Set-Location $RepoRoot

Write-Host "[roadmap-authority] RepoRoot: $RepoRoot" -ForegroundColor Cyan

$activeScopes = @(
    '.ai',
    '.github',
    'scripts'
)

$allowedExtensions = @(
    '.ps1', '.psm1', '.py', '.yml', '.yaml', '.json'
)

$excludedFileRegexes = @(
    '\.bak$',
    '\.backup($|_)',
    '\.tmp$',
    '\.old$',
    '\.orig$',
    '\.disabled$'
)

$excludedPathRegexes = @(
    '[\\/]\.tmp[\\/]',
    '[\\/]\.roadmap_archive[\\/]',
    '[\\/]ARCHIVE[\\/]',
    '[\\/]backup[\\/]'
)

$excludedLeafNames = @(
    'reject-roadmap-shadow-authorities.ps1',
    'repair-roadmap-authority.ps1'
)

$allowedCanonicalRegexes = @(
    'docs[\\/]governance[\\/]ROADMAP_CURRENT\.json'
    'repo_root\s*/\s*["'']docs["'']\s*/\s*["'']governance["'']\s*/\s*["'']ROADMAP_CURRENT\.json["'']'
)

$execViolationRegexes = @(
    'Join-Path\s+[^`r`n]+["''](?:AUDIT[\\/])?ROADMAP_CURRENT\.json["'']',
    'Test-Path\s+["''](?:AUDIT[\\/])?ROADMAP_CURRENT\.json["'']',
    'ReadAllBytes\(\s*["''](?:AUDIT[\\/])?ROADMAP_CURRENT\.json["'']\s*\)',
    'Get-Content\s+[^`r`n]*["''](?:AUDIT[\\/])?ROADMAP_CURRENT\.json["'']',
    'Set-Content\s+[^`r`n]*["''](?:AUDIT[\\/])?ROADMAP_CURRENT\.json["'']',
    'WriteAllText\(\s*[^`r`n]*["''](?:AUDIT[\\/])?ROADMAP_CURRENT\.json["'']',
    'open\(\s*["''](?:AUDIT[\\/])?ROADMAP_CURRENT\.json["'']',
    'repo_root\s*\/\s*["''](?:AUDIT[\\/])?ROADMAP_CURRENT\.json["'']',
    'Path\(\s*["''](?:AUDIT[\\/])?ROADMAP_CURRENT\.json["'']\s*\)',
    '["''][^"'']*(?:AUDIT[\\/])?ROADMAP_CURRENT\.json["'']'
)

$violations = New-Object System.Collections.Generic.List[object]

function Test-ExcludedPath {
    param([string]$Path)

    $normalized = $Path -replace '/', '\'

    foreach ($rx in $excludedPathRegexes) {
        if ($normalized -match $rx) { return $true }
    }

    foreach ($rx in $excludedFileRegexes) {
        if ($normalized -match $rx) { return $true }
    }

    return $false
}

function Test-ExcludedFile {
    param([System.IO.FileInfo]$File)

    if ($File.Extension -notin $allowedExtensions) {
        return $true
    }

    if ($File.Name -in $excludedLeafNames) {
        return $true
    }

    if (Test-ExcludedPath -Path $File.FullName) {
        return $true
    }

    return $false
}

function Test-AllowedCanonical {
    param([string]$Line)

    foreach ($rx in $allowedCanonicalRegexes) {
        if ($Line -match $rx) { return $true }
    }

    return $false
}

function Test-ExecutableViolation {
    param([string]$Line)

    if ($Line -notmatch 'ROADMAP_CURRENT\.json') {
        return $false
    }

    if (Test-AllowedCanonical -Line $Line) {
        return $false
    }

    foreach ($rx in $execViolationRegexes) {
        if ($Line -match $rx) {
            return $true
        }
    }

    return $false
}

foreach ($scope in $activeScopes) {
    if (-not (Test-Path $scope)) { continue }

    Get-ChildItem -Path $scope -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $file = $_

        if (Test-ExcludedFile -File $file) {
            return
        }

        $relativePath = Resolve-Path -Relative $file.FullName
        $lineNumber = 0

        foreach ($line in [System.IO.File]::ReadLines($file.FullName)) {
            $lineNumber++

            if (-not (Test-ExecutableViolation -Line $line)) {
                continue
            }

            $violations.Add([PSCustomObject]@{
                File = $relativePath
                Line = $lineNumber
                Content = $line.Trim()
            })
        }
    }
}

if ($violations.Count -gt 0) {
    Write-Host ""
    Write-Host "[roadmap-authority] Executable shadow authority references detected." -ForegroundColor Red
    Write-Host ""

    foreach ($v in $violations) {
        Write-Host (" - {0}:{1}: {2}" -f $v.File, $v.Line, $v.Content) -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "[roadmap-authority] Allowed canonical reference:" -ForegroundColor Cyan
    Write-Host "   docs/governance/ROADMAP_CURRENT.json" -ForegroundColor Green
    Write-Host ""
    Write-Host "[roadmap-authority] Failing build." -ForegroundColor Red
    exit 1
}

Write-Host "[roadmap-authority] PASS: no executable shadow roadmap authority references found." -ForegroundColor Green
exit 0
