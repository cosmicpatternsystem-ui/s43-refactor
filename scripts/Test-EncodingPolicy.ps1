param(
    [Parameter(Mandatory = $false)]
    [string]$RepoRoot = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Test-IsTextExtension {
    param(
        [Parameter(Mandatory = $false)]
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Extension
    )

    if ([string]::IsNullOrWhiteSpace($Extension)) {
        return $false
    }

    $textExtensions = @(
        '.ps1', '.psm1', '.psd1',
        '.py',
        '.json', '.jsonl',
        '.yml', '.yaml',
        '.md', '.txt',
        '.js', '.jsx', '.ts', '.tsx',
        '.css', '.scss',
        '.html',
        '.sh', '.bash',
        '.toml', '.ini', '.cfg',
        '.csv'
    )

    return $Extension.ToLowerInvariant() -in $textExtensions
}

function Test-IsExcludedPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $normalized = $RelativePath -replace '/', '\'

    $excludedPrefixes = @(
        '.git\',
        '.ai\',
        'runtime\',
        '.venv\',
        'venv\',
        '__pycache__\',
        '.pytest_cache\',
        '.mypy_cache\',
        '.vscode\',
        '.idea\',
        'node_modules\',
        'dist\',
        'build\',
        '.next\',
        '.roadmap_journal\',
        'BASELINE_PROTECTION_SNAPSHOT_',
        'READ_ONLY_FEATURE_AUDIT_',
        'TRACEABILITY_FINALIZER_',
        'TRACEABILITY_GAP_PHASE',
        'repair_backup_',
        'roadmap_governance_evidence\',
        'RESTORE_TESTS\'
    )

    foreach ($prefix in $excludedPrefixes) {
        if ($normalized.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }

    $fileName = [System.IO.Path]::GetFileName($normalized)

    if ($fileName -match '(^|_)\d{8,}(_\d+)?\.log$') { return $true }
    if ($fileName -like '*.log') { return $true }
    if ($fileName -like '*.tmp') { return $true }
    if ($fileName -like '*.bak') { return $true }
    if ($fileName -like '*.pyc') { return $true }
    if ($fileName -like '*.pyo') { return $true }

    return $false
}

function Test-IsIncludedPhasePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $normalized = $RelativePath -replace '/', '\'

    $includedExact = @(
        'scripts\Test-Durability.ps1',
        'scripts\Test-EncodingPolicy.ps1',
        'scripts\Test-RepoHygiene.ps1'
    )

    foreach ($item in $includedExact) {
        if ($normalized.Equals($item, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }

    if ($normalized.StartsWith('tests\powershell\', [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }

    return $false
}

function Test-FileEncodingPolicy {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $bytes = [System.IO.File]::ReadAllBytes($Path)

    if ($bytes.Length -eq 0) {
        return
    }

    if ($bytes.Length -ge 3) {
        if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
            throw "BOM detected: $Path"
        }
    }

    foreach ($b in $bytes) {
        if ($b -eq 0x0D) {
            throw "CR byte detected: $Path"
        }
    }

    if ($bytes[$bytes.Length - 1] -ne 0x0A) {
        throw "Missing final LF: $Path"
    }
}

$repoRootFull = [System.IO.Path]::GetFullPath($RepoRoot)

$files = Get-ChildItem -LiteralPath $repoRootFull -Recurse -File | Where-Object {
    $full = $_.FullName
    $relative = $full.Substring($repoRootFull.Length).TrimStart('\','/')

    if ([string]::IsNullOrWhiteSpace($relative)) {
        return $false
    }

    if (Test-IsExcludedPath -RelativePath $relative) {
        return $false
    }

    if (-not (Test-IsIncludedPhasePath -RelativePath $relative)) {
        return $false
    }

    return (Test-IsTextExtension -Extension $_.Extension)
} | Sort-Object FullName

foreach ($file in $files) {
    Test-FileEncodingPolicy -Path $file.FullName
}

Write-Host ("Encoding policy OK: {0} files checked" -f $files.Count)
