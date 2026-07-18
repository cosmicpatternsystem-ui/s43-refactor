Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_mcp03-env.ps1')

$repoRoot = Get-Mcp03RepoRoot
$artifactRoot = Get-Mcp03ArtifactRoot -RepoRoot $repoRoot
$replayRoot = Join-Path $artifactRoot 'replay'
$outputPath = Join-Path $replayRoot 'mcp03-replay-smoke.json'

New-Item -ItemType Directory -Force -Path $replayRoot | Out-Null

Push-Location $repoRoot
try {
  Enter-Mcp03PythonEnv -RepoRoot $repoRoot

  python -m pytest tests/replay -q
  if ($LASTEXITCODE -ne 0) {
    throw "Replay smoke failed with exit code $LASTEXITCODE"
  }

  $payload = [ordered]@{
    project = 'MCP-03'
    generated_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'passed'
    suite = 'replay-smoke'
    target = 'tests/replay'
  }

  Write-Utf8NoBomLf -Path $outputPath -Content ($payload | ConvertTo-Json -Depth 10)
  Write-Host "Wrote $outputPath"
}
finally {
  Pop-Location
}