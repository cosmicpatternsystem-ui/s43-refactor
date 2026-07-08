#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

Write-Host "AI Context Verification Test" -ForegroundColor Cyan
Write-Host ("=" * 60)

$questions = @(
    @{ Q = "Mission ASO-X?"; Expected = "Global Financial Intelligence" },
    @{ Q = "Why atomic write critical?"; Expected = "Data loss unacceptable" },
    @{ Q = "Source of Truth?"; Expected = "repository_files_only" },
    @{ Q = "Push to main allowed?"; Expected = "No, PR only" },
    @{ Q = "JSON encoding?"; Expected = "BOM-free UTF-8 LF" },
    @{ Q = "Current phase?"; Expected = "Phase B1" }
)

Write-Host "`nTest Questions:" -ForegroundColor Yellow
$i = 1
foreach ($item in $questions) {
    Write-Host "[$i] $($item.Q)"
    Write-Host "    Expected: $($item.Expected)" -ForegroundColor Green
    $i++
}

Write-Host "`n" + ("=" * 60)
Write-Host "If AI answers all, context OK" -ForegroundColor Green