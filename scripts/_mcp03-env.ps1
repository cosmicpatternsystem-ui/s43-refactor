Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Mcp03RepoRoot {
  (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
}

function Get-Mcp03ArtifactRoot {
  param([Parameter(Mandatory = $true)][string]$RepoRoot)
  Join-Path $RepoRoot 'artifacts'
}

function Write-Utf8NoBomLf {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Content
  )

  $dir = Split-Path -Parent $Path
  if ($dir -and -not (Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
  }

  $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
  [System.IO.File]::WriteAllText($Path, ($Content -replace "
", "
"), $utf8NoBom)
}

function Enter-Mcp03PythonEnv {
  param([Parameter(Mandatory = $true)][string]$RepoRoot)

  $srcPath = Join-Path $RepoRoot 'src'
  $existing = [Environment]::GetEnvironmentVariable('PYTHONPATH', 'Process')

  if ([string]::IsNullOrWhiteSpace($existing)) {
    [Environment]::SetEnvironmentVariable('PYTHONPATH', $srcPath, 'Process')
  }
  elseif (($existing -split ';') -notcontains $srcPath) {
    [Environment]::SetEnvironmentVariable('PYTHONPATH', "$srcPath;$existing", 'Process')
  }
}