[CmdletBinding()]
param(
    [switch]$Autonomous,
    [switch]$VerboseMode
)

$ErrorActionPreference = 'Stop'

function Write-Log {
    param(
        [Parameter(Mandatory=$true)][string]$Message,
        [ValidateSet('INFO','WARN','ERROR','DEBUG')][string]$Level = 'INFO'
    )

    if ($Level -eq 'DEBUG' -and -not $VerboseMode) { return }
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Write-Host "[$ts] [$Level] $Message"
}

function Mask-Secret {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return 'MISSING' }
    $len = $Value.Length
    if ($len -le 8) { return ('*' * $len) }
    $prefix = $Value.Substring(0,4)
    $suffix = $Value.Substring($len-4,4)
    return "$prefix...$suffix"
}

function Test-CommandExists {
    param([Parameter(Mandatory=$true)][string]$Command)
    try {
        $null = Get-Command $Command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

try {
    Write-Log "========================================" "INFO"
    Write-Log "S43 Auto Safe Launcher" "INFO"
    Write-Log "========================================" "INFO"

    $ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
    $ProjectRoot = Split-Path -Parent $ScriptDir
    $RuntimeFile = Join-Path $ProjectRoot 'MY_S43_LATEST.py'

    if (-not (Test-Path -LiteralPath $RuntimeFile)) {
        throw "Runtime file not found: $RuntimeFile"
    }

    $PythonCandidates = @(
        $env:PYTHON_EXE,
        (Join-Path $ProjectRoot '.venv\Scripts\python.exe'),
        (Join-Path $ProjectRoot 'venv\Scripts\python.exe'),
        'python',
        'py'
    ) | Where-Object { $_ -and $_.Trim() -ne '' }

    $PythonExe = $null
    foreach ($candidate in $PythonCandidates) {
        try {
            if ($candidate -match '\.exe$') {
                if (Test-Path -LiteralPath $candidate) {
                    $PythonExe = $candidate
                    break
                }
            } else {
                if (Test-CommandExists -Command $candidate) {
                    $PythonExe = $candidate
                    break
                }
            }
        } catch {}
    }

    if (-not $PythonExe) {
        throw "Python executable not found. Checked: $($PythonCandidates -join ', ')"
    }

    $Wallet1 = $env:ARZPLUS_WALLET_1_TOKEN
    $Wallet2 = $env:ARZPLUS_WALLET_2_TOKEN
    $Wallet3 = $env:ARZPLUS_WALLET_3_TOKEN

    $Wallet1Present = -not [string]::IsNullOrWhiteSpace($Wallet1)
    $Wallet2Present = -not [string]::IsNullOrWhiteSpace($Wallet2)
    $Wallet3Present = -not [string]::IsNullOrWhiteSpace($Wallet3)
    $AllTokensPresent = $Wallet1Present -and $Wallet2Present -and $Wallet3Present

    $SiblingRoot = Split-Path -Parent $ProjectRoot
    if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
        $env:PYTHONPATH = "$ProjectRoot;$SiblingRoot"
    } else {
        $env:PYTHONPATH = "$ProjectRoot;$SiblingRoot;$($env:PYTHONPATH)"
    }

    if ([string]::IsNullOrWhiteSpace($env:AUTONOMOUS_AI)) {
        $env:AUTONOMOUS_AI = 'True'
    }
    if ([string]::IsNullOrWhiteSpace($env:OPENAI_TRADE_ENABLE)) {
        $env:OPENAI_TRADE_ENABLE = 'True'
    }

    Write-Log "ProjectRoot              = $ProjectRoot" "INFO"
    Write-Log "RuntimeFile              = $RuntimeFile" "INFO"
    Write-Log "PythonExe                = $PythonExe" "INFO"
    Write-Log "AUTONOMOUS_AI            = $($env:AUTONOMOUS_AI)" "INFO"
    Write-Log "OPENAI_TRADE_ENABLE      = $($env:OPENAI_TRADE_ENABLE)" "INFO"
    Write-Log "Wallet1                  = $(Mask-Secret $Wallet1)" "INFO"
    Write-Log "Wallet2                  = $(Mask-Secret $Wallet2)" "INFO"
    Write-Log "Wallet3                  = $(Mask-Secret $Wallet3)" "INFO"
    Write-Log "AllTokensPresent         = $AllTokensPresent" "INFO"

    Write-Log "ScriptDir                = $ScriptDir" "DEBUG"
    Write-Log "SiblingRoot              = $SiblingRoot" "DEBUG"
    Write-Log "PYTHONPATH               = $($env:PYTHONPATH)" "DEBUG"
    Write-Log "CurrentLocation          = $(Get-Location)" "DEBUG"
    Write-Log "PowerShellVersion        = $($PSVersionTable.PSVersion)" "DEBUG"

    if (-not $AllTokensPresent) {
        Write-Log "One or more required wallet tokens are missing. Aborting startup." "ERROR"
        exit 10
    }

    $ArgsList = @($RuntimeFile)

    if ($Autonomous) {
        Write-Log "Autonomous live mode requested." "INFO"

        $env:LIVE_TRADING = '1'
        $env:LIVE_TRADING_ARMED = 'True'
        $env:ARZPLUS_LIVE_ARMED = 'True'
        $env:AI_LIVE_TRADING_ARMED = 'True'
        $env:AUTONOMOUS_AI = 'True'
        $env:OPENAI_TRADE_ENABLE = 'True'
        $env:S43_LOCAL_LIVE_OVERRIDE = '1'
        $env:OFFLINE_OVERRIDE = '1'
        $env:S43_FALLBACK_MODE = '0'

        Write-Log "LIVE_TRADING            = $($env:LIVE_TRADING)" "INFO"
        Write-Log "LIVE_TRADING_ARMED      = $($env:LIVE_TRADING_ARMED)" "INFO"
        Write-Log "ARZPLUS_LIVE_ARMED      = $($env:ARZPLUS_LIVE_ARMED)" "INFO"
        Write-Log "AI_LIVE_TRADING_ARMED   = $($env:AI_LIVE_TRADING_ARMED)" "INFO"
        Write-Log "S43_LOCAL_LIVE_OVERRIDE = $($env:S43_LOCAL_LIVE_OVERRIDE)" "INFO"
        Write-Log "OFFLINE_OVERRIDE        = $($env:OFFLINE_OVERRIDE)" "INFO"
        Write-Log "S43_FALLBACK_MODE       = $($env:S43_FALLBACK_MODE)" "INFO"

        $ArgsList += '--live'
    }
    else {
        Write-Log "Environment ready. Starting in safe status mode." "INFO"
        $ArgsList += '--status'
    }

    $DisplayCommand = "$PythonExe " + ($ArgsList -join ' ')
    Write-Log "Executing: $DisplayCommand" "INFO"

    Push-Location $ProjectRoot
    try {
        if ($PythonExe -eq 'py') {
            & py @ArgsList
        } elseif ($PythonExe -eq 'python') {
            & python @ArgsList
        } else {
            & $PythonExe @ArgsList
        }
        $ExitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    if ($null -eq $ExitCode) { $ExitCode = 0 }
    if ($ExitCode -ne 0) {
        Write-Log "Runtime exited with code: $ExitCode" "ERROR"
        exit $ExitCode
    }

    Write-Log "Runtime completed successfully." "INFO"
    exit 0
}
catch {
    Write-Log $_.Exception.Message "ERROR"
    exit 1
}
