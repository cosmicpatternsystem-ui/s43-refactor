param()

$ErrorActionPreference = "Stop"

Write-Host "Approval record validation:" -ForegroundColor Cyan

$recordDir = ".\governance\approval_records"

if (-not (Test-Path $recordDir)) {
    Write-Host "OK  no approval_records directory present"
    return
}

$records = Get-ChildItem -Path $recordDir -Filter "*.md" -File

if (-not $records) {
    Write-Host "OK  no approval records present"
    return
}

$allowedDecisions = @(
    "APPROVED_FOR_GOVERNANCE_ONLY",
    "APPROVED_FOR_SINGLE_POINT_IMPLEMENTATION_REVIEW",
    "REJECTED",
    "DEFERRED"
)

$failed = $false

foreach ($record in $records) {
    $raw = Get-Content -Path $record.FullName -Raw

    # Validate only the filled record section, not the appended template reference.
    $recordSection = ($raw -split '(?m)^## Template Reference\s*$')[0]

    if ($recordSection -match '\b(REQUIRED|TODO|TBD)\b') {
        Write-Host "BLOCK  $($record.FullName) contains unresolved placeholders"
        $failed = $true
    }

    $decisionMatch = [regex]::Match(
        $recordSection,
        '(?m)^\s*-\s*Approval decision:\s*(\S+)\s*$'
    )

    if (-not $decisionMatch.Success) {
        Write-Host "BLOCK  $($record.FullName) missing Approval decision"
        $failed = $true
    } elseif ($allowedDecisions -notcontains $decisionMatch.Groups[1].Value) {
        Write-Host "BLOCK  $($record.FullName) has invalid Approval decision: $($decisionMatch.Groups[1].Value)"
        $failed = $true
    }

    if ($recordSection -notmatch '(?m)^\s*-\s*Target file:\s*\S+') {
        Write-Host "BLOCK  $($record.FullName) missing Target file"
        $failed = $true
    }

    if ($recordSection -notmatch '(?m)^\s*-\s*Target function or insertion point:\s*\S+') {
        Write-Host "BLOCK  $($record.FullName) missing Target function or insertion point"
        $failed = $true
    }
}

if ($failed) {
    throw "Approval record validation failed."
}

Write-Host "OK  approval records complete"
