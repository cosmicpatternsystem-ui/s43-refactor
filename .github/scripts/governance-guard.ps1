#requires -Version 7.0
# governance-guard.ps1 — pre-commit governance gate (Resolver architecture)
# Exit codes:
#   0   = pass
#   101 = wrong PowerShell major version
#   102 = required governance file missing
#   103 = python interpreter unavailable
#   104 = resolver contract check failed
#   105 = roadmap authority validation failed
#   201 = unexpected internal error

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Fail {
    param([int]$Code, [string]$Message)
    # NOTE: no Write-Error here — under EAP=Stop it becomes terminating
    # and the exit line would never run. Console stderr is safe.
    [Console]::Error.WriteLine("GOVERNANCE-GUARD FAIL($Code): $Message")
    exit $Code
}

try {
    # --- 1. Runtime guard -------------------------------------------------
    if ($PSVersionTable.PSVersion.Major -lt 7) {
        Fail 101 "PowerShell 7+ required; running $($PSVersionTable.PSVersion)."
    }

    $repoRoot = (& git rev-parse --show-toplevel 2>$null)
    if (-not $repoRoot) { Fail 201 'Cannot resolve git repository root.' }
    Set-Location $repoRoot

    # --- 2. Required governance files (Resolver architecture) ------------
    $expected = @(
        'tools/governance.ps1',
        'scripts/resolve_next_action.py',
        'tools/roadmap_sync.py',
        'tools/durable_state.py',
        'docs/governance/ROADMAP_CANONICAL.md',
        'docs/governance/ROADMAP_CURRENT.json',
        'docs/governance/ROADMAP_MANIFEST.json'
    )
    $missing = @($expected | Where-Object { -not (Test-Path (Join-Path $repoRoot $_)) })
    if ($missing.Count -gt 0) {
        Fail 102 ("Required governance files missing: " + ($missing -join ', '))
    }

    # --- 3. Python availability ------------------------------------------
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { Fail 103 'python not found on PATH.' }

    # --- 4. Resolver contract check --------------------------------------
    # CRITICAL: initialize before any native-exit check (StrictMode-safe)
    $global:LASTEXITCODE = 0
    & python scripts/resolve_next_action.py --help *> $null
    if ($LASTEXITCODE -ne 0) {
        Fail 104 "Resolver contract check failed (exit $LASTEXITCODE)."
    }

    # --- 5. Roadmap authority validation ----------------------------------
    $validatorPath = Join-Path $repoRoot 'tools/validate-roadmap-authority.ps1'
    if (-not (Test-Path $validatorPath)) {
        $validatorPath = Join-Path $repoRoot 'scripts/validate-roadmap-authority.ps1'
    }
    if (Test-Path $validatorPath) {
        $global:LASTEXITCODE = 0
        & pwsh -NoProfile -File $validatorPath
        if ($LASTEXITCODE -ne 0) {
            Fail 105 "Roadmap authority validation failed (exit $LASTEXITCODE)."
        }
    } else {
        Fail 102 'validate-roadmap-authority.ps1 not found in tools/ or scripts/.'
    }

    Write-Host 'GOVERNANCE-GUARD: PASS'
    exit 0
}
catch {
    [Console]::Error.WriteLine("GOVERNANCE-GUARD FAIL(201): $($_.Exception.Message)")
    exit 201
}