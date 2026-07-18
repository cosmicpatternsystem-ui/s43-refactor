Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_mcp03-env.ps1')

$repoRoot = Get-Mcp03RepoRoot

$targets = @(
  'src/aso_x',
  'tests/unit',
  'tests/property',
  'tests/replay',
  'formal/z3'
) | Where-Object { Test-Path -LiteralPath (Join-Path $repoRoot $_) }

if (-not $targets -or $targets.Count -eq 0) {
  throw 'No MCP-03 static-analysis targets found.'
}

Push-Location $repoRoot
try {
  Enter-Mcp03PythonEnv -RepoRoot $repoRoot

  python -m ruff check @targets
  if ($LASTEXITCODE -ne 0) {
    throw "ruff failed with exit code $LASTEXITCODE"
  }

  python -m mypy --disable-error-code import-untyped @targets
  if ($LASTEXITCODE -ne 0) {
    throw "mypy failed with exit code $LASTEXITCODE"
  }
}
finally {
  Pop-Location
}