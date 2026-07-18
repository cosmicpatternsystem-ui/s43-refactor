Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_mcp03-env.ps1')

$repoRoot = Get-Mcp03RepoRoot

Push-Location $repoRoot
try {
  Enter-Mcp03PythonEnv -RepoRoot $repoRoot

  python -m pytest tests/property -q
  if ($LASTEXITCODE -ne 0) {
    throw "Property tests failed with exit code $LASTEXITCODE"
  }
}
finally {
  Pop-Location
}