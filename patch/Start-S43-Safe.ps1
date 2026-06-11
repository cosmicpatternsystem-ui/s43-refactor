[CmdletBinding()]
param(
    [switch]$Autonomous,
    [switch]$VerboseMode
)

$ErrorActionPreference = "Stop"

try {
    $ScriptDir = $PSScriptRoot

    if ([string]::IsNullOrWhiteSpace($ScriptDir)) {
        if (-not [string]::IsNullOrWhiteSpace($MyInvocation.MyCommand.Path)) {
            $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        }
        else {
            throw "This launcher must be run from a saved .ps1 file."
        }
    }

    $ProjectRoot = Split-Path -Parent $ScriptDir
    $SiblingRoot = Split-Path -Parent $ProjectRoot
    $PythonFile  = Join-Path $ProjectRoot "MY_S43_LATEST.py"

    if (-not (Test-Path -LiteralPath $ProjectRoot)) {
        throw "Project root not found: $ProjectRoot"
    }

    if (-not (Test-Path -LiteralPath $PythonFile)) {
        throw "Python runtime file not found: $PythonFile"
    }

    $env:AUTONOMOUS_AI = "True"
    $env:OPENAI_TRADE_ENABLE = "True"

    $PathParts = @($ProjectRoot, $SiblingRoot)

    if (-not [string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
        $PathParts += $env:PYTHONPATH
    }

    $env:PYTHONPATH = ($PathParts -join ';')

    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "S43 Safe Launcher" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "ProjectRoot         = $ProjectRoot"
    Write-Host "PythonFile          = $PythonFile"
    Write-Host "AUTONOMOUS_AI       = $env:AUTONOMOUS_AI"
    Write-Host "OPENAI_TRADE_ENABLE = $env:OPENAI_TRADE_ENABLE"

    if ($VerboseMode) {
        Write-Host "ScriptDir           = $ScriptDir"
        Write-Host "SiblingRoot         = $SiblingRoot"
        Write-Host "PYTHONPATH          = $env:PYTHONPATH"
        Write-Host "Current Location    = $(Get-Location)"
        Write-Host "PowerShell Version  = $($PSVersionTable.PSVersion)"
    }

    $missing = @()

    if ([string]::IsNullOrWhiteSpace($env:WALLET_1_TOKEN)) {
        $missing += "WALLET_1_TOKEN"
    }

    if ([string]::IsNullOrWhiteSpace($env:WALLET_2_TOKEN)) {
        $missing += "WALLET_2_TOKEN"
    }

    if ([string]::IsNullOrWhiteSpace($env:WALLET_3_TOKEN)) {
        $missing += "WALLET_3_TOKEN"
    }

    if (-not $Autonomous) {
        Write-Host "[SAFE-DEFAULT] Launching status mode only..." -ForegroundColor Yellow
        & python $PythonFile --status
        exit $LASTEXITCODE
    }

    if ($missing.Count -gt 0) {
        Write-Host "[SAFE-BLOCK] Missing wallet token environment variables:" -ForegroundColor Yellow

        foreach ($m in $missing) {
            Write-Host " - $m" -ForegroundColor Yellow
        }

        Write-Host "Falling back to status mode..." -ForegroundColor Yellow
        & python $PythonFile --status
        exit $LASTEXITCODE
    }

    Write-Host "[AUTONOMOUS] Tokens detected. Launching autonomous mode..." -ForegroundColor Green
    & python $PythonFile --autonomous
    exit $LASTEXITCODE
}
catch {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "LAUNCH FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
