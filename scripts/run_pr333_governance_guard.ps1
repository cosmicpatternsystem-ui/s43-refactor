$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

function Fail([string]$msg) {
    Write-Host ""
    Write-Host "FAIL-CLOSED: $msg" -ForegroundColor Red
    exit 1
}

$repo = (& git rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($repo)) {
    Fail "Not inside a git repository."
}

$repo = $repo.Trim()
Set-Location $repo

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    $py = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $py) {
    Fail "Python launcher not found. Expected python or py."
}

& $py.Source "scripts/guard_pr333_governance_atomicity.py"
if ($LASTEXITCODE -ne 0) {
    Fail "PR333 governance atomicity guard failed."
}

& $py.Source "scripts/validate_mcp03_invariants.py"
if ($LASTEXITCODE -ne 0) {
    Fail "MCP03 invariant validator failed."
}

& $py.Source "tools/governance/validate_roadmap_authority.py"
if ($LASTEXITCODE -ne 0) {
    Fail "Roadmap authority validator failed."
}

Write-Host ""
Write-Host "PASS: PR333 governance guard runner completed." -ForegroundColor Green
