#requires -Version 5.1
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Utf8NoBomAtomic {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $dir = Split-Path -Parent $fullPath

    if (-not [string]::IsNullOrWhiteSpace($dir) -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }

    $tmp = Join-Path $dir (([System.IO.Path]::GetFileName($fullPath)) + '.tmp.' + [guid]::NewGuid().ToString('N'))
    $enc = New-Object System.Text.UTF8Encoding($false)

    try {
        $fs = [System.IO.File]::Open($tmp, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        try {
            $sw = New-Object System.IO.StreamWriter($fs, $enc)
            try {
                $sw.Write($Content)
                $sw.Flush()
                $fs.Flush($true)
            }
            finally {
                $sw.Dispose()
            }
        }
        finally {
            $fs.Dispose()
        }

        if (Test-Path -LiteralPath $fullPath) {
            try {
                [System.IO.File]::Replace($tmp, $fullPath, $null)
            }
            catch {
                Remove-Item -LiteralPath $fullPath -Force -ErrorAction SilentlyContinue
                [System.IO.File]::Move($tmp, $fullPath)
            }
        }
        else {
            [System.IO.File]::Move($tmp, $fullPath)
        }
    }
    finally {
        if (Test-Path -LiteralPath $tmp) {
            Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        }
    }
}

function Normalize-Json {
    param(
        [Parameter(Mandatory = $true)][object]$Object
    )
    return ($Object | ConvertTo-Json -Depth 32)
}

$repoRoot = (Get-Location).Path
$toolsDir = Join-Path $repoRoot 'tools'
$logsDir = Join-Path $repoRoot 'logs'
$stateDir = Join-Path $repoRoot 'state'
$outDir = Join-Path $repoRoot 'out'
$quarantineDir = Join-Path $repoRoot 'quarantine'

$null = New-Item -ItemType Directory -Force -Path $toolsDir, $logsDir, $stateDir, $outDir, $quarantineDir

$governanceConfig = @'
{
  "$schema": "./governance.schema.json",
  "version": 1,
  "governance": {
    "mutexName": "Global\\S43.ExternalFileGovernance",
    "ledgerPath": "./state/governance-ledger.jsonl",
    "logPath": "./logs/governance-log.jsonl",
    "quarantineDir": "./quarantine",
    "manifestPath": "./out/governance-manifest.json",
    "auditCsvPath": "./out/governance-audit.csv",
    "evidenceDir": "./out/evidence",
    "retentionDays": 30,
    "secretPatterns": [
      "(?i)password",
      "(?i)secret",
      "(?i)token",
      "(?i)apikey",
      "(?i)private[_-]?key"
    ]
  }
}
'@

$governanceSchema = @'
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ASO-X Governance Config",
  "type": "object",
  "required": ["version", "governance"],
  "properties": {
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "governance": {
      "type": "object",
      "required": [
        "mutexName",
        "ledgerPath",
        "logPath",
        "quarantineDir",
        "manifestPath",
        "auditCsvPath",
        "evidenceDir",
        "retentionDays",
        "secretPatterns"
      ],
      "properties": {
        "mutexName": { "type": "string", "minLength": 1 },
        "ledgerPath": { "type": "string", "minLength": 1 },
        "logPath": { "type": "string", "minLength": 1 },
        "quarantineDir": { "type": "string", "minLength": 1 },
        "manifestPath": { "type": "string", "minLength": 1 },
        "auditCsvPath": { "type": "string", "minLength": 1 },
        "evidenceDir": { "type": "string", "minLength": 1 },
        "retentionDays": { "type": "integer", "minimum": 1 },
        "secretPatterns": {
          "type": "array",
          "items": { "type": "string" }
        }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": true
}
'@

$bootstrapScript = @'
#requires -Version 5.1
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$required = @(
    (Join-Path $PSScriptRoot 'governance.ps1'),
    (Join-Path $PSScriptRoot 'governance.config.json'),
    (Join-Path $PSScriptRoot 'governance.schema.json'),
    (Join-Path $PSScriptRoot 'self-test-governance.ps1')
)

foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing required file: $path"
    }
}

$dirs = @(
    (Join-Path $repoRoot 'logs'),
    (Join-Path $repoRoot 'state'),
    (Join-Path $repoRoot 'out'),
    (Join-Path $repoRoot 'quarantine'),
    (Join-Path $repoRoot 'out\evidence')
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

Write-Host "bootstrap-governance: OK"
'@

$selfTestScript = @'
#requires -Version 5.1
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$gov = Join-Path $PSScriptRoot 'governance.ps1'
$config = Join-Path $PSScriptRoot 'governance.config.json'
$schema = Join-Path $PSScriptRoot 'governance.schema.json'

foreach ($path in @($gov, $config, $schema)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing required file: $path"
    }
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $gov health-check | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "health-check failed with exit code $LASTEXITCODE"
}

Write-Host "self-test-governance: OK"
'@

$governanceScript = @'
#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("health-check","run","register-task","show-task")]
    [string]$Command = "run",

    [string]$ConfigPath = (Join-Path $PSScriptRoot "governance.config.json"),

    [string]$TaskName = "S43 External File Governance",

    [string]$DailyAt = "21:00"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Utf8NoBomAtomic {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $dir = Split-Path -Parent $fullPath

    if (-not [string]::IsNullOrWhiteSpace($dir) -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }

    $tmp = Join-Path $dir (([System.IO.Path]::GetFileName($fullPath)) + ".tmp." + [guid]::NewGuid().ToString("N"))
    $enc = New-Object System.Text.UTF8Encoding($false)

    try {
        $fs = [System.IO.File]::Open($tmp, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        try {
            $sw = New-Object System.IO.StreamWriter($fs, $enc)
            try {
                $sw.Write($Content)
                $sw.Flush()
                $fs.Flush($true)
            }
            finally {
                $sw.Dispose()
            }
        }
        finally {
            $fs.Dispose()
        }

        if (Test-Path -LiteralPath $fullPath) {
            try {
                [System.IO.File]::Replace($tmp, $fullPath, $null)
            }
            catch {
                Remove-Item -LiteralPath $fullPath -Force -ErrorAction SilentlyContinue
                [System.IO.File]::Move($tmp, $fullPath)
            }
        }
        else {
            [System.IO.File]::Move($tmp, $fullPath)
        }
    }
    finally {
        if (Test-Path -LiteralPath $tmp) {
            Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        }
    }
}

function Resolve-RepoPath {
    param([Parameter(Mandatory = $true)][string]$Path)
    $root = Split-Path -Parent $PSScriptRoot
    return [System.IO.Path]::GetFullPath((Join-Path $root $Path))
}

function Get-Config {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Config not found: $Path"
    }
    return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
}

function New-JsonLine {
    param([Parameter(Mandatory = $true)][hashtable]$Data)
    return ($Data | ConvertTo-Json -Depth 16 -Compress)
}

function Add-JsonLine {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][hashtable]$Data
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $dir = Split-Path -Parent $fullPath
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }

    $line = (New-JsonLine -Data $Data) + [Environment]::NewLine
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::AppendAllText($fullPath, $line, $enc)
}

function Get-FileSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Test-SecretLikeFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Patterns
    )

    try {
        $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 -ErrorAction Stop
    }
    catch {
        return $false
    }

    foreach ($pattern in $Patterns) {
        if ($content -match $pattern) {
            return $true
        }
    }
    return $false
}

function Invoke-HealthCheck {
    param([Parameter(Mandatory = $true)]$Config)

    $paths = @(
        (Resolve-RepoPath $Config.governance.ledgerPath),
        (Resolve-RepoPath $Config.governance.logPath),
        (Resolve-RepoPath $Config.governance.quarantineDir),
        (Resolve-RepoPath $Config.governance.evidenceDir)
    )

    foreach ($path in $paths) {
        $parent = $path
        if ([System.IO.Path]::HasExtension($path)) {
            $parent = Split-Path -Parent $path
        }
        if (-not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Force -Path $parent | Out-Null
        }
    }

    Write-Host "health-check: OK"
}

function Invoke-Run {
    param([Parameter(Mandatory = $true)]$Config)

    $mutexName = $Config.governance.mutexName
    $mutex = New-Object System.Threading.Mutex($false, $mutexName)
    $lockTaken = $false

    try {
        $lockTaken = $mutex.WaitOne([TimeSpan]::FromSeconds(30))
        if (-not $lockTaken) {
            throw "Failed to acquire mutex: $mutexName"
        }

        $repoRoot = Split-Path -Parent $PSScriptRoot
        $ledgerPath = Resolve-RepoPath $Config.governance.ledgerPath
        $logPath = Resolve-RepoPath $Config.governance.logPath
        $manifestPath = Resolve-RepoPath $Config.governance.manifestPath
        $auditCsvPath = Resolve-RepoPath $Config.governance.auditCsvPath
        $quarantineDir = Resolve-RepoPath $Config.governance.quarantineDir
        $evidenceDir = Resolve-RepoPath $Config.governance.evidenceDir

        $null = New-Item -ItemType Directory -Force -Path $quarantineDir, $evidenceDir, (Split-Path -Parent $ledgerPath), (Split-Path -Parent $logPath), (Split-Path -Parent $manifestPath), (Split-Path -Parent $auditCsvPath)

        $files = Get-ChildItem -LiteralPath $repoRoot -Recurse -File -Force |
            Where-Object {
                $_.FullName -notmatch [regex]::Escape("\.git\") -and
                $_.FullName -notmatch [regex]::Escape("\quarantine\") -and
                $_.FullName -notmatch [regex]::Escape("\out\evidence\")
            }

        $rows = New-Object System.Collections.Generic.List[object]
        $manifestItems = New-Object System.Collections.Generic.List[object]
        $patterns = @($Config.governance.secretPatterns)

        foreach ($file in $files) {
            $relative = $file.FullName.Substring($repoRoot.Length).TrimStart("\")
            $sha256 = Get-FileSha256 -Path $file.FullName
            $isSecretLike = Test-SecretLikeFile -Path $file.FullName -Patterns $patterns

            if ($isSecretLike) {
                $target = Join-Path $quarantineDir $relative
                $targetDir = Split-Path -Parent $target
                if (-not (Test-Path -LiteralPath $targetDir)) {
                    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
                }
                Copy-Item -LiteralPath $file.FullName -Destination $target -Force
            }

            $row = [pscustomobject]@{
                path = $relative
                size = $file.Length
                lastWriteTimeUtc = $file.LastWriteTimeUtc.ToString("o")
                sha256 = $sha256
                secretLike = $isSecretLike
            }
            $rows.Add($row) | Out-Null
            $manifestItems.Add($row) | Out-Null
        }

        $manifest = [ordered]@{
            generatedAtUtc = [DateTime]::UtcNow.ToString("o")
            machine = $env:COMPUTERNAME
            user = $env:USERNAME
            itemCount = $manifestItems.Count
            items = $manifestItems
        }

        $csv = $rows | ConvertTo-Csv -NoTypeInformation
        Write-Utf8NoBomAtomic -Path $auditCsvPath -Content ($csv -join [Environment]::NewLine)

        $manifestJson = $manifest | ConvertTo-Json -Depth 32
        Write-Utf8NoBomAtomic -Path $manifestPath -Content $manifestJson

        Add-JsonLine -Path $ledgerPath -Data @{
            ts = [DateTime]::UtcNow.ToString("o")
            event = "run"
            itemCount = $manifestItems.Count
            manifestSha256 = (Get-FileSha256 -Path $manifestPath)
            auditSha256 = (Get-FileSha256 -Path $auditCsvPath)
        }

        Add-JsonLine -Path $logPath -Data @{
            ts = [DateTime]::UtcNow.ToString("o")
            level = "info"
            action = "run"
            status = "ok"
            itemCount = $manifestItems.Count
        }

        $evidence = [ordered]@{
            generatedAtUtc = [DateTime]::UtcNow.ToString("o")
            manifestPath = $manifestPath
            auditCsvPath = $auditCsvPath
            ledgerPath = $ledgerPath
            logPath = $logPath
        }
        $evidencePath = Join-Path $evidenceDir ("evidence-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".json")
        Write-Utf8NoBomAtomic -Path $evidencePath -Content ($evidence | ConvertTo-Json -Depth 16)

        Write-Host "run: OK"
        Write-Host ("manifest: " + $manifestPath)
        Write-Host ("audit: " + $auditCsvPath)
    }
    finally {
        if ($lockTaken) {
            [void]$mutex.ReleaseMutex()
        }
        $mutex.Dispose()
    }
}

function Register-GovernanceTask {
    param(
        [Parameter(Mandatory = $true)][string]$TaskName,
        [Parameter(Mandatory = $true)][string]$DailyAt
    )

    $govPath = Join-Path $PSScriptRoot "governance.ps1"
    $time = [datetime]::ParseExact($DailyAt, "HH:mm", $null)

    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$govPath`" run"
    $trigger = New-ScheduledTaskTrigger -Daily -At $time.TimeOfDay
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null
    Write-Host "register-task: OK"
}

function Show-GovernanceTask {
    param([Parameter(Mandatory = $true)][string]$TaskName)
    Get-ScheduledTask -TaskName $TaskName | Format-List *
}

$config = Get-Config -Path $ConfigPath

switch ($Command) {
    "health-check" { Invoke-HealthCheck -Config $config; break }
    "run"          { Invoke-Run -Config $config; break }
    "register-task" { Register-GovernanceTask -TaskName $TaskName -DailyAt $DailyAt; break }
    "show-task"    { Show-GovernanceTask -TaskName $TaskName; break }
    default        { throw "Unknown command: $Command" }
}
'@

Write-Utf8NoBomAtomic -Path (Join-Path $toolsDir 'governance.config.json') -Content $governanceConfig
Write-Utf8NoBomAtomic -Path (Join-Path $toolsDir 'governance.schema.json') -Content $governanceSchema
Write-Utf8NoBomAtomic -Path (Join-Path $toolsDir 'bootstrap-governance.ps1') -Content $bootstrapScript
Write-Utf8NoBomAtomic -Path (Join-Path $toolsDir 'self-test-governance.ps1') -Content $selfTestScript
Write-Utf8NoBomAtomic -Path (Join-Path $toolsDir 'governance.ps1') -Content $governanceScript

Write-Host "apply-enterprise-governance: OK"
Write-Host ("wrote: " + (Join-Path $toolsDir 'governance.ps1'))
Write-Host ("wrote: " + (Join-Path $toolsDir 'governance.config.json'))
Write-Host ("wrote: " + (Join-Path $toolsDir 'governance.schema.json'))
Write-Host ("wrote: " + (Join-Path $toolsDir 'bootstrap-governance.ps1'))
Write-Host ("wrote: " + (Join-Path $toolsDir 'self-test-governance.ps1'))
