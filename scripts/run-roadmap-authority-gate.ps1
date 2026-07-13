$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = (& git rev-parse --show-toplevel).Trim()
Set-Location $RepoRoot

$python = (Get-Command python -ErrorAction Stop).Source
& $python "tools/governance/validate_roadmap_authority.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python -m pytest "tests/test_roadmap_governance.py" -q
exit $LASTEXITCODE