$ErrorActionPreference = 'Stop'

$ScriptPath = $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($ScriptPath)) {
    throw 'Unable to resolve script path.'
}

$ProjectRoot = Split-Path -Parent $ScriptPath
$CanonicalFile = Join-Path $ProjectRoot 's43_instrumented_LATEST.py'
$ExcludedFile = Join-Path $ProjectRoot 's43_latest_refactor.py'
$ComparisonFile = Join-Path $ProjectRoot 'MY_S43_LATEST.py'

$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$RunDir = Join-Path $ProjectRoot ("auto_safe_ai_gate_patch_{0}" -f $Timestamp)
$BackupDir = Join-Path $RunDir 'backup'
$ReportPath = Join-Path $RunDir 'PATCH_REPORT.md'
$PyCompileLog = Join-Path $RunDir 'py_compile.log'

$TargetLineNumber = 20101
$AnchorPattern = 'if getattr\(self, "_ai_trader", None\) is not None'
$RequiredGuards = @(
    'getattr(self, "_capital_kill_switch", False)',
    'not getattr(self, "_daily_loss_reached", False)',
    'not getattr(self, "_session_lock_active", False)'
)

$Status = 'UNKNOWN'
$Message = ''
$Patched = $false
$RollbackPerformed = $false
$BeforeSha256 = ''
$AfterSha256 = ''

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Find-Python {
    $candidates = @('python', 'py')
    foreach ($candidate in $candidates) {
        try {
            & $candidate --version *> $null
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        }
        catch {
        }
    }

    throw 'Python executable not found in PATH.'
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Write-Report {
    $lines = @(
        '# PATCH REPORT',
        '',
        ('Timestamp: {0}' -f $Timestamp),
        ('ProjectRoot: {0}' -f $ProjectRoot),
        ('CanonicalFile: {0}' -f $CanonicalFile),
        ('ExcludedFile: {0}' -f $ExcludedFile),
        ('ComparisonFile: {0}' -f $ComparisonFile),
        ('TargetLine: {0}' -f $TargetLineNumber),
        ('Status: {0}' -f $Status),
        ('Message: {0}' -f $Message),
        ('Patched: {0}' -f $Patched),
        ('RollbackPerformed: {0}' -f $RollbackPerformed),
        ('BeforeSHA256: {0}' -f $BeforeSha256),
        ('AfterSHA256: {0}' -f $AfterSha256),
        ('PyCompileLog: {0}' -f $PyCompileLog)
    )

    Set-Content -LiteralPath $ReportPath -Value $lines -Encoding UTF8
}

function Get-FileLines {
    param([Parameter(Mandatory = $true)][string]$Path)

    @(Get-Content -LiteralPath $Path)
}

function Find-GateIndex {
    param([AllowNull()][object[]]$Lines)

    if ($null -eq $Lines -or $Lines.Count -eq 0) {
        return -1
    }

    $start = [Math]::Max(0, $TargetLineNumber - 6)
    $end = [Math]::Min($Lines.Count - 1, $TargetLineNumber + 6)

    for ($i = $start; $i -le $end; $i++) {
        if ([string]$Lines[$i] -match $AnchorPattern) {
            return $i
        }
    }

    for ($i = 0; $i -lt $Lines.Count; $i++) {
        if ([string]$Lines[$i] -match $AnchorPattern) {
            return $i
        }
    }

    return -1
}

function Test-GateLineContainsAllGuards {
    param([Parameter(Mandatory = $true)][string]$LineContent)

    foreach ($guard in $RequiredGuards) {
        if ($LineContent -notmatch [regex]::Escape($guard)) {
            return $false
        }
    }

    return $true
}

function Invoke-PyCompile {
    param(
        [Parameter(Mandatory = $true)][string]$PythonCommand,
        [Parameter(Mandatory = $true)][string]$TargetFile,
        [Parameter(Mandatory = $true)][string]$LogPath
    )

    $output = & $PythonCommand -m py_compile $TargetFile 2>&1
    Set-Content -LiteralPath $LogPath -Value @($output) -Encoding UTF8

    if ($LASTEXITCODE -ne 0) {
        throw 'py_compile failed.'
    }
}

Ensure-Directory -Path $RunDir
Ensure-Directory -Path $BackupDir

try {
    if (-not (Test-Path -LiteralPath $CanonicalFile)) {
        throw 'Canonical target file not found.'
    }

    if (-not (Test-Path -LiteralPath $ExcludedFile)) {
        throw 'Excluded file not found.'
    }

    $PythonExe = Find-Python
    $BeforeSha256 = Get-Sha256 -Path $CanonicalFile
    $allLines = @(Get-FileLines -Path $CanonicalFile)
    $gateIndex = Find-GateIndex -Lines $allLines

    if ($gateIndex -lt 0) {
        $Status = 'SKIPPED'
        $Message = 'Anchor not found; fail-closed skip.'
        $AfterSha256 = $BeforeSha256
        Write-Report
        Write-Output 'SKIPPED'
        exit 0
    }

    $lineContent = [string]$allLines[$gateIndex]

    if (Test-GateLineContainsAllGuards -LineContent $lineContent) {
        $Status = 'SKIPPED'
        $Message = 'AI gate already hardened.'
        $AfterSha256 = $BeforeSha256
        Write-Report
        Write-Output 'SKIPPED'
        exit 0
    }

    Copy-Item -LiteralPath $CanonicalFile -Destination (Join-Path $BackupDir 's43_instrumented_LATEST.py.bak') -Force

    $updatedLine = $lineContent.TrimEnd(':')
    foreach ($guard in $RequiredGuards) {
        if ($updatedLine -notmatch [regex]::Escape($guard)) {
            $updatedLine += (' and {0}' -f $guard)
        }
    }
    $updatedLine += ':'

    $allLines[$gateIndex] = $updatedLine
    Set-Content -LiteralPath $CanonicalFile -Value $allLines -Encoding UTF8
    $Patched = $true
    $AfterSha256 = Get-Sha256 -Path $CanonicalFile

    Invoke-PyCompile -PythonCommand $PythonExe -TargetFile $CanonicalFile -LogPath $PyCompileLog

    $postLines = @(Get-FileLines -Path $CanonicalFile)
    if ($gateIndex -ge $postLines.Count) {
        throw 'Post-patch gate index out of range.'
    }

    if (-not (Test-GateLineContainsAllGuards -LineContent ([string]$postLines[$gateIndex]))) {
        throw 'Post-patch guard verification failed.'
    }

    $Status = 'PATCHED'
    $Message = 'AI gate hardened successfully.'
    Write-Report
    Write-Output 'PATCHED'
    exit 0
}
catch {
    $Message = $_.Exception.Message

    $backupFile = Join-Path $BackupDir 's43_instrumented_LATEST.py.bak'
    if ($Patched -and (Test-Path -LiteralPath $backupFile)) {
        Copy-Item -LiteralPath $backupFile -Destination $CanonicalFile -Force
        $RollbackPerformed = $true
        $AfterSha256 = Get-Sha256 -Path $CanonicalFile
    }
    elseif ([string]::IsNullOrWhiteSpace($AfterSha256)) {
        $AfterSha256 = $BeforeSha256
    }

    $Status = 'ROLLED_BACK'
    Write-Report
    Write-Output 'ROLLED_BACK'
    exit 1
}
