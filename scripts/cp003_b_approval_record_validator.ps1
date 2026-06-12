param(
    [string]$RecordsPath = ".\governance\approval_records"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Approval record validation:" -ForegroundColor Cyan

if (-not (Test-Path $RecordsPath)) {
    Write-Host "OK  no approval_records directory present"
    exit 0
}

$records = Get-ChildItem -Path $RecordsPath -Filter "*.md" -File | Sort-Object Name
if (-not $records) {
    Write-Host "OK  no approval record files present"
    exit 0
}

$failed = $false

foreach ($record in $records) {
    $content = Get-Content -Path $record.FullName -Raw

    if ($content -match '\bREQUIRED\b' -or $content -match '\bTODO\b' -or $content -match '\bTBD\b') {
        Write-Host "BLOCK  $($record.FullName) contains unresolved placeholders" -ForegroundColor Yellow
        $failed = $true
    }

    $decisionMatch = [regex]::Match($content, '(?mi)^Approval decision:\s*(.+?)\s*$')
    if (-not $decisionMatch.Success) {
        Write-Host "BLOCK  $($record.FullName) missing Approval decision" -ForegroundColor Yellow
        $failed = $true
    } else {
        $decisionValue = $decisionMatch.Groups[1].Value.Trim()
        if ([string]::IsNullOrWhiteSpace($decisionValue)) {
            Write-Host "BLOCK  $($record.FullName) has empty Approval decision" -ForegroundColor Yellow
            $failed = $true
        }
    }

    $targetFileMatch = [regex]::Match($content, '(?mi)^Target file:\s*(.+?)\s*$')
    if (-not $targetFileMatch.Success) {
        Write-Host "BLOCK  $($record.FullName) missing Target file" -ForegroundColor Yellow
        $failed = $true
    }

    $insertionPointMatch = [regex]::Match($content, '(?mi)^Insertion point:\s*(.+?)\s*$')
    if (-not $insertionPointMatch.Success) {
        Write-Host "BLOCK  $($record.FullName) missing Insertion point" -ForegroundColor Yellow
        $failed = $true
    }

    if (-not $failed) {
        Write-Host "OK  $($record.FullName)"
    }
}

if ($failed) {
    throw "Approval record validation failed."
}
