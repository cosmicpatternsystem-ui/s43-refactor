$ErrorActionPreference = "Stop"
function Write-Ok($m){ Write-Host "[OK]   $m" -ForegroundColor Green }
function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Fail($m){ Write-Host "[FAIL] $m" -ForegroundColor Red }
$root = Get-Location
$mainFiles = @("s43_instrumented_LATEST.py", "s43_latest_refactor.py", "MY_S43_LATEST.py")
$outDir = Join-Path $root ("safe_patch_proposal_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
foreach($f in $mainFiles){ if(Test-Path $f){ Copy-Item $f (Join-Path $outDir ($f + ".bak")) -Force } }
Write-Ok "Backup created in $outDir"
$proposalPath = Join-Path $outDir "PATCH_PROPOSAL.md"
"## Safe Patch Proposal

Evidence-based patch proposal for AI safety." | Set-Content $proposalPath
Write-Ok "Proposal created: $proposalPath"
