param(
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message"
}

function Require-File {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Required file missing: $Path"
    }

    Write-Host "OK: $Path"
}

function Test-ExcludedPath {
    param([string]$Path)

    $normalized = $Path -replace "\\", "/"

    $excludedSegments = @(
        "/.git/",
        "/node_modules/",
        "/.next/",
        "/dist/",
        "/build/",
        "/coverage/",
        "/.venv/",
        "/venv/",
        "/__pycache__/",
        "/.pytest_cache/"
    )

    foreach ($segment in $excludedSegments) {
        if ($normalized.Contains($segment)) {
            return $true
        }
    }

    return $false
}

Write-Host "SECURITY_BASELINE_AUDIT_START"
Write-Host "Mode: non-destructive local audit"
Write-Host "Secret values: never printed"

Write-Step "validate git repository"
$insideGit = git rev-parse --is-inside-work-tree
if ($insideGit -ne "true") {
    throw "Not inside a Git repository."
}
Write-Host "OK: git repository detected"

Write-Step "show branch"
$branch = git branch --show-current
Write-Host "Branch: $branch"

Write-Step "show working tree status"
$status = git status --short
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "Working tree: clean"
} else {
    Write-Host "Working tree has changes:"
    Write-Host $status
    if ($Strict) {
        throw "Strict mode requires a clean working tree."
    }
}

Write-Step "validate mandatory roadmap files"
Require-File "AUDIT/COMMERCIAL_MANDATORY_ROADMAP.md"
Require-File "AUDIT/NEXT_ACTION.md"

Write-Step "collect candidate files"
$root = (Get-Location).Path

$allFiles = Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { -not (Test-ExcludedPath -Path $_.FullName) }

Write-Host ("Files inspected: {0}" -f $allFiles.Count)

Write-Step "check high-risk file names"
$riskyNamePatterns = @(
    '\.env$',
    '\.env\.',
    'id_rsa$',
    'id_dsa$',
    '\.pem$',
    '\.key$',
    'credentials\.',
    'secrets\.',
    'service-account.*\.json$'
)

$riskyFiles = New-Object System.Collections.Generic.List[string]

foreach ($file in $allFiles) {
    $relative = $file.FullName.Substring($root.Length).TrimStart('\', '/')
    $relativeForMatch = $relative -replace "\\", "/"

    foreach ($pattern in $riskyNamePatterns) {
        if ($relativeForMatch -match $pattern) {
            $riskyFiles.Add($relativeForMatch)
            break
        }
    }
}

if ($riskyFiles.Count -eq 0) {
    Write-Host "High-risk file names: none detected"
} else {
    Write-Host ("High-risk file names detected: {0}" -f $riskyFiles.Count)
    $riskyFiles | Sort-Object -Unique | ForEach-Object {
        Write-Host ("RISK_FILE: {0}" -f $_)
    }
}

Write-Step "check suspicious secret patterns"
$patternMap = [ordered]@{
    "API_KEY_ASSIGNMENT" = '(?i)(api[_-]?key)\s*[:=]\s*["''][^"'']{8,}["'']'
    "ACCESS_TOKEN_ASSIGNMENT" = '(?i)(access[_-]?token)\s*[:=]\s*["''][^"'']{8,}["'']'
    "SECRET_KEY_ASSIGNMENT" = '(?i)(secret[_-]?key)\s*[:=]\s*["''][^"'']{8,}["'']'
    "PASSWORD_ASSIGNMENT" = '(?i)(password|passwd|pwd)\s*[:=]\s*["''][^"'']{8,}["'']'
    "BEARER_TOKEN" = '(?i)bearer\s+[a-z0-9\._\-]{20,}'
    "AWS_ACCESS_KEY_ID" = 'AKIA[0-9A-Z]{16}'
    "GITHUB_TOKEN" = 'gh[pousr]_[A-Za-z0-9_]{20,}'
    "STRIPE_KEY" = 'sk_(live|test)_[A-Za-z0-9]{16,}'
    "PRIVATE_KEY_BLOCK" = '-----BEGIN [A-Z ]*PRIVATE KEY-----'
    "JWT_LIKE_TOKEN" = 'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'
}

$findings = New-Object System.Collections.Generic.List[string]

$textExtensions = @(
    ".ps1", ".psm1", ".psd1", ".md", ".txt", ".json", ".yaml", ".yml", ".toml",
    ".ini", ".env", ".example", ".js", ".jsx", ".ts", ".tsx", ".py", ".cs",
    ".java", ".go", ".rs", ".php", ".rb", ".sh", ".bat", ".cmd", ".html",
    ".css", ".scss", ".sql", ".xml"
)

foreach ($file in $allFiles) {
    if ($file.Length -gt 1048576) {
        continue
    }

    $ext = [System.IO.Path]::GetExtension($file.Name)
    if ($textExtensions -notcontains $ext -and $file.Name -notmatch '^\.env') {
        continue
    }

    $relative = $file.FullName.Substring($root.Length).TrimStart('\', '/') -replace "\\", "/"

    try {
        $content = [System.IO.File]::ReadAllText($file.FullName)
    } catch {
        continue
    }

    foreach ($label in $patternMap.Keys) {
        if ($content -match $patternMap[$label]) {
            $findings.Add(("{0} :: {1}" -f $relative, $label))
        }
    }
}

if ($findings.Count -eq 0) {
    Write-Host "Suspicious secret patterns: none detected"
} else {
    Write-Host ("Suspicious secret pattern findings: {0}" -f $findings.Count)
    $findings | Sort-Object -Unique | ForEach-Object {
        Write-Host ("PATTERN_FINDING: {0}" -f $_)
    }

    Write-Host ""
    Write-Host "Important: Values were intentionally not printed."
    Write-Host "Manual review is required before declaring these real secrets."
}

Write-Step "security baseline checklist"
Write-Host "Require secrets handling policy."
Write-Host "Require environment file policy."
Write-Host "Require dependency audit policy."
Write-Host "Require static security scan policy."
Write-Host "Require sensitive logging policy."
Write-Host "Require authentication review."
Write-Host "Require authorization review."
Write-Host "Require incident response path."
Write-Host "Require remediation plan for confirmed findings."

Write-Step "non-destructive guarantee"
Write-Host "No secrets printed."
Write-Host "No files modified."
Write-Host "No credentials rotated."
Write-Host "No production service contacted."
Write-Host "No infrastructure changed."

Write-Host ""
Write-Host "SECURITY_BASELINE_AUDIT_PASS"