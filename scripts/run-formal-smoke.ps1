Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_mcp03-env.ps1')

$repoRoot = Get-Mcp03RepoRoot
$artifactRoot = Get-Mcp03ArtifactRoot -RepoRoot $repoRoot
$formalRoot = Join-Path $artifactRoot 'formal'
$outputPath = Join-Path $formalRoot 'mcp03-formal-smoke.json'

New-Item -ItemType Directory -Force -Path $formalRoot | Out-Null

Push-Location $repoRoot
try {
  Enter-Mcp03PythonEnv -RepoRoot $repoRoot

  python -m pytest formal/z3 -q
  if ($LASTEXITCODE -ne 0) {
    throw "Formal smoke failed with exit code $LASTEXITCODE"
  }

  $payload = [ordered]@{
    project = 'MCP-03'
    generated_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'passed'
    suite = 'formal-smoke'
    target = 'formal/z3'
  }

  Write-Utf8NoBomLf -Path $outputPath -Content ($payload | ConvertTo-Json -Depth 10)
  Write-Host "Wrote $outputPath"
}
finally {
  Pop-Location
}