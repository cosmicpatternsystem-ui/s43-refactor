#!/usr/bin/env pwsh
<#
.SYNOPSIS
    AI Onboarding Script - ASO-X Context Loader
#>

param([switch]$Verbose)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "AI Context Loader v1.0" -ForegroundColor Cyan
Write-Host ("=" * 60)

Write-Host "`n[1/5] Git Repository Status" -ForegroundColor Yellow
$branch = git branch --show-current 2>$null
$commit = git log -1 --format="%h - %s" 2>$null
$status = git status --porcelain 2>$null

if ($branch) {
    Write-Host "   Branch:  $branch"
    Write-Host "   Commit:  $commit"
    if ($status) {
        Write-Host "   Status:  DIRTY" -ForegroundColor Red
        if ($Verbose) { git status --short }
    } else {
        Write-Host "   Status:  CLEAN" -ForegroundColor Green
    }
} else {
    Write-Host "   Not a Git repository" -ForegroundColor Yellow
}

Write-Host "`n[2/5] Critical Files" -ForegroundColor Yellow
if ($PSScriptRoot) {
    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
} else {
    $repoRoot = (Get-Location).Path
}

$handoffPath = Join-Path $repoRoot "HANDOFF.md"
$phaseChecklistPath = Join-Path $repoRoot "docs/PHASE_B1_CHECKLIST.md"
$onboardingPath = Join-Path $repoRoot "docs/AI_ONBOARDING.md"
$canonicalRoadmapCurrent = Join-Path $repoRoot "docs/governance/ROADMAP_CURRENT.json"
$validateRoadmapScript = Join-Path $repoRoot "scripts/validate-roadmap.ps1"

$criticalFiles = @(
    $handoffPath,
    $phaseChecklistPath,
    $onboardingPath,
    $canonicalRoadmapCurrent,
    $validateRoadmapScript
)

foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        Write-Host "   OK $file" -ForegroundColor Green
    } else {
        Write-Host "   MISSING $file" -ForegroundColor Red
    }
}

Write-Host "`n[3/5] Project Context" -ForegroundColor Yellow
if (Test-Path "HANDOFF.md") {
    Write-Host "   Reading HANDOFF.md..." -ForegroundColor Cyan
}

Write-Host "`n[4/5] Standards Check" -ForegroundColor Yellow
if (Test-Path $canonicalRoadmapCurrent) {
    $bytes = [System.IO.File]::ReadAllBytes($canonicalRoadmapCurrent)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        Write-Host "   BOM detected" -ForegroundColor Red
    } else {
        Write-Host "   BOM-free OK" -ForegroundColor Green
    }
}

Write-Host "`n[5/5] Next Steps" -ForegroundColor Yellow
Write-Host "   1. Read HANDOFF.md"
Write-Host "   2. Read docs/AI_ONBOARDING.md"
Write-Host "   3. Read docs/PHASE_B1_CHECKLIST.md"

Write-Host "`n" + ("=" * 60)
Write-Host "Context Load Complete" -ForegroundColor Green