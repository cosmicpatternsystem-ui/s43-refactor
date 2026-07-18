Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_mcp03-env.ps1')

$repoRoot = Get-Mcp03RepoRoot
$artifactRoot = Get-Mcp03ArtifactRoot -RepoRoot $repoRoot
$formalSmokePath = Join-Path $artifactRoot 'formal\mcp03-formal-smoke.json'
$replaySmokePath = Join-Path $artifactRoot 'replay\mcp03-replay-smoke.json'
$outputPath = Join-Path $artifactRoot 'mcp03-evidence.json'

if (-not (Test-Path -LiteralPath $formalSmokePath)) {
  throw "Required artifact missing: $formalSmokePath"
}

$formalSmoke = Get-Content -LiteralPath $formalSmokePath -Raw | ConvertFrom-Json

$replaySmoke = $null
if (Test-Path -LiteralPath $replaySmokePath) {
  $replaySmoke = Get-Content -LiteralPath $replaySmokePath -Raw | ConvertFrom-Json
}

$payload = [ordered]@{
  project = 'MCP-03'
  generated_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  status = 'passed'
  evidence = [ordered]@{
    formal_smoke = $formalSmoke
    replay_smoke = $replaySmoke
  }
  docs = @(
    'docs/governance/MCP_03_CORRECTNESS_ENVELOPE.md',
    'docs/governance/MCP_03_INVARIANTS.md'
  )
  source_roots = @(
    'src/aso_x',
    'tests/unit',
    'tests/property',
    'tests/replay',
    'formal/z3'
  )
}

Write-Utf8NoBomLf -Path $outputPath -Content ($payload | ConvertTo-Json -Depth 10)
Write-Host "Wrote $outputPath"