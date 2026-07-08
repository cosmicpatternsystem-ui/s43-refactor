param([switch]$AllowDirty)
$ErrorActionPreference = "Stop"
function Fail($m) { Write-Host "FAIL: $m" -ForegroundColor Red; exit 1 }
function Pass($m) { Write-Host "PASS: $m" -ForegroundColor Green }
$repoRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0 -or -not $repoRoot) { $repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..") }
$repoRoot = "$repoRoot".Trim()
Set-Location $repoRoot
$policyPath = Join-Path $repoRoot "AUDIT/RELEASE_READINESS_POLICY.json"
if (-not (Test-Path $policyPath)) { Fail "Missing policy" }
$policy = Get-Content $policyPath -Raw | ConvertFrom-Json
$masterPath = Join-Path $repoRoot $policy.canonical_master
if (-not (Test-Path $masterPath)) { Fail "Missing master" }
foreach ($e in $policy.required_evidence) { if (-not (Test-Path (Join-Path $repoRoot $e))) { Fail "Missing evidence: $e" } }
$master = Get-Content $masterPath -Raw
foreach ($p in $policy.required_master_phrases) { if ($master -notlike "*$p*") { Fail "Master missing phrase: $p" } }
$status = git status --porcelain
if (-not $AllowDirty -and -not [string]::IsNullOrWhiteSpace($status)) { Fail "Working tree is dirty" }
Pass "Policy exists"
Pass "Canonical master exists"
Pass "Required evidence exists"
Pass "Master contains required phrases"
Pass "Repository state is acceptable"
Write-Host ""
Write-Host "RELEASE READINESS GATE: PASS" -ForegroundColor Green
