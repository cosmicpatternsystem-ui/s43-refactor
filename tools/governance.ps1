# Authority: docs/governance/ROADMAP_CANONICAL.md (via Resolver)
#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = $PSScriptRoot | Split-Path -Parent
$ResolverScript = Join-Path $RepoRoot 'scripts/resolve_next_action.py'

if (-not (Test-Path $ResolverScript)) {
    Write-Error "Resolver not found: $ResolverScript"
    exit 1
}

python $ResolverScript @args
exit $LASTEXITCODE