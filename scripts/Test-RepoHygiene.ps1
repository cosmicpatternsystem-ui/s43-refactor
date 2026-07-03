[CmdletBinding()]
param(
    [string]$RepoRoot
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
        $RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
    }
    else {
        $RepoRoot = (Get-Location).Path
    }
}

Push-Location $RepoRoot
try {
    $status = git status --short
    if ($LASTEXITCODE -ne 0) {
        throw "git status failed"
    }

    $bad = @()
    foreach ($line in $status) {
        if ($line -match '\.tmp$' -or $line -match '\.bak$') {
            $bad += $line
        }
    }

    if ($bad.Count -gt 0) {
        throw ("Transient artifacts detected:`n" + ($bad -join "`n"))
    }

    Write-Host "[OK] Repo hygiene check passed" -ForegroundColor Green
}
finally {
    Pop-Location
}
