param(
    [Parameter(Position = 0)]
    [ValidateSet('health-check', 'run', 'register-task', 'unregister-task', 'self-test', 'validate')]
    [string]$Command = 'health-check',

    [string]$TaskName = 'ASO-X Governance Daily',
    [string]$TaskTime = '03:15'
)

$ErrorActionPreference = 'Stop'

function Get-ScriptRootStrict {
    if ($MyInvocation.MyCommand.Path) {
        return [System.IO.Path]::GetDirectoryName([System.IO.Path]::GetFullPath($MyInvocation.MyCommand.Path))
    }
    if ($PSCommandPath) {
        return [System.IO.Path]::GetDirectoryName([System.IO.Path]::GetFullPath($PSCommandPath))
    }
    return (Get-Location).Path
}

$script:ScriptRoot = Get-ScriptRootStrict
$script:RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $script:ScriptRoot '..'))
$script:ConfigPath = Join-Path $script:ScriptRoot 'governance.config.json'

function ConvertTo-Utf8NoBomJson {
    param(
        [Parameter(Mandatory = $true)]$InputObject,
        [switch]$Compress
    )

    if ($Compress) {
        return ($InputObject | ConvertTo-Json -Depth 20 -Compress)
    }

    return ($InputObject | ConvertTo-Json -Depth 20)
}

function Write-Utf8NoBomAtomic {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $directory = [System.IO.Path]::GetDirectoryName($fullPath)

    if ([string]::IsNullOrWhiteSpace($directory)) {
        throw "Invalid target directory for path: $Path"
    }

    if (-not (Test-Path -LiteralPath $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }

    $tempPath = Join-Path $directory ('.tmp-' + [System.Guid]::NewGuid().ToString('N'))
    $encoding = New-Object System.Text.UTF8Encoding($false)

    [System.IO.File]::WriteAllText($tempPath, $Content, $encoding)

    if (Test-Path -LiteralPath $fullPath) {
        Remove-Item -LiteralPath $fullPath -Force
    }

    Move-Item -LiteralPath $tempPath -Destination $fullPath -Force
}

function Add-Utf8NoBomLineAtomic {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Line
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $directory = [System.IO.Path]::GetDirectoryName($fullPath)

    if (-not (Test-Path -LiteralPath $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }

    $existing = ''
    if (Test-Path -LiteralPath $fullPath) {
        $existing = [System.IO.File]::ReadAllText($fullPath, [System.Text.Encoding]::UTF8)
    }

    if ($existing.Length -gt 0 -and -not $existing.EndsWith("`n")) {
        $existing += "`n"
    }

    Write-Utf8NoBomAtomic -Path $fullPath -Content ($existing + $Line + "`n")
}

function Resolve-RepoPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath((Join-Path $script:RepoRoot $Path))
}

function Read-GovernanceConfig {
    if (-not (Test-Path -LiteralPath $script:ConfigPath)) {
        throw "Missing governance config: $script:ConfigPath"
    }

    $config = Get-Content -LiteralPath $script:ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json

    if (-not $config.governance) {
        throw "Invalid config: missing governance object"
    }

    return $config
}

function Get-GovernancePaths {
    $config = Read-GovernanceConfig
    $governance = $config.governance

    $ledgerPath = Resolve-RepoPath ([string]$governance.ledgerPath)
    $logPath = Resolve-RepoPath ([string]$governance.logPath)
    $manifestPath = Resolve-RepoPath ([string]$governance.manifestPath)
    $auditCsvPath = Resolve-RepoPath ([string]$governance.auditCsvPath)
    $evidenceDir = Resolve-RepoPath ([string]$governance.evidenceDir)

    return [pscustomobject]@{
        Config = $config
        LedgerPath = $ledgerPath
        LogPath = $logPath
        ManifestPath = $manifestPath
        AuditCsvPath = $auditCsvPath
        EvidenceDir = $evidenceDir
    }
}

function Write-GovernanceLog {
    param(
        [Parameter(Mandatory = $true)][string]$Event,
        [string]$Level = 'INFO',
        [hashtable]$Data = @{}
    )

    $paths = Get-GovernancePaths

    $entry = [ordered]@{
        ts = [DateTime]::UtcNow.ToString('o')
        level = $Level
        event = $Event
        machine = $env:COMPUTERNAME
        user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
        repoRoot = $script:RepoRoot
        data = $Data
    }

    $line = ConvertTo-Utf8NoBomJson $entry -Compress
    Add-Utf8NoBomLineAtomic -Path $paths.LogPath -Line $line
}

function Write-GovernanceLedger {
    param(
        [Parameter(Mandatory = $true)][string]$Event,
        [hashtable]$Data = @{}
    )

    $paths = Get-GovernancePaths

    $entry = [ordered]@{
        ts = [DateTime]::UtcNow.ToString('o')
        event = $Event
    }

    foreach ($key in $Data.Keys) {
        $entry[$key] = $Data[$key]
    }

    $line = ConvertTo-Utf8NoBomJson $entry -Compress
    Add-Utf8NoBomLineAtomic -Path $paths.LedgerPath -Line $line
}

function Test-SecretLikeContent {
    param([Parameter(Mandatory = $true)][string]$Path)

    $maxBytes = 1048576
    $fileInfo = Get-Item -LiteralPath $Path -Force

    if ($fileInfo.Length -gt $maxBytes) {
        return $false
    }

    try {
        $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 -ErrorAction Stop
    } catch {
        return $false
    }

    $patterns = @(
        'AKIA[0-9A-Z]{16}',
        '-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
        '(?i)\b(api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*["''][^"'']{8,}["'']',
        '(?i)\bghp_[A-Za-z0-9_]{30,}\b',
        '(?i)\bsk-[A-Za-z0-9]{20,}\b'
    )

    foreach ($pattern in $patterns) {
        if ($content -match $pattern) {
            return $true
        }
    }

    return $false
}

function Get-RepoFilesForAudit {
    $paths = Get-GovernancePaths
    $config = $paths.Config
    $excludeDirs = @()

    if ($config.governance.excludeDirs) {
        $excludeDirs = @($config.governance.excludeDirs | ForEach-Object { [string]$_ })
    }

    $repoRootPrefix = $script:RepoRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar

    Get-ChildItem -LiteralPath $script:RepoRoot -File -Recurse -Force | Where-Object {
        $fullName = $_.FullName
        $relative = $fullName.Substring($repoRootPrefix.Length)
        $parts = $relative -split '[\\/]'

        foreach ($part in $parts) {
            if ($excludeDirs -contains $part) {
                return $false
            }
        }

        return $true
    }
}

function ConvertTo-RelativeRepoPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $prefix = $script:RepoRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar

    if ($fullPath.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        return ($fullPath.Substring($prefix.Length) -replace '\\', '/')
    }

    return $fullPath
}

function New-GovernanceAudit {
    $paths = Get-GovernancePaths

    if (-not (Test-Path -LiteralPath $paths.EvidenceDir)) {
        New-Item -ItemType Directory -Path $paths.EvidenceDir -Force | Out-Null
    }

    Write-GovernanceLog -Event 'run.start' -Data @{ command = 'run' }

    $rows = New-Object System.Collections.Generic.List[object]
    $manifestItems = New-Object System.Collections.Generic.List[object]

    foreach ($file in Get-RepoFilesForAudit) {
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        $relativePath = ConvertTo-RelativeRepoPath $file.FullName
        $secretLike = Test-SecretLikeContent -Path $file.FullName

        $rows.Add([pscustomobject]@{
            path = $relativePath
            size = [int64]$file.Length
            sha256 = $hash
            secretLike = [bool]$secretLike
        }) | Out-Null

        $manifestItems.Add([ordered]@{
            path = $relativePath
            size = [int64]$file.Length
            sha256 = $hash
            lastWriteTimeUtc = $file.LastWriteTimeUtc.ToString('o')
            secretLike = [bool]$secretLike
        }) | Out-Null
    }

    $csv = ($rows | Sort-Object path | ConvertTo-Csv -NoTypeInformation)
    Write-Utf8NoBomAtomic -Path $paths.AuditCsvPath -Content (($csv -join "`r`n") + "`r`n")

    $manifest = [ordered]@{
        schema = 'aso-x.governance.manifest.v1'
        generatedAtUtc = [DateTime]::UtcNow.ToString('o')
        machine = $env:COMPUTERNAME
        repoRoot = $script:RepoRoot
        itemCount = $manifestItems.Count
        items = @($manifestItems | Sort-Object { $_.path })
    }

    Write-Utf8NoBomAtomic -Path $paths.ManifestPath -Content ((ConvertTo-Utf8NoBomJson $manifest) + "`n")

    Write-GovernanceLedger -Event 'run' -Data @{ itemCount = $manifestItems.Count }
    Write-GovernanceLog -Event 'run.complete' -Data @{
        itemCount = $manifestItems.Count
        auditCsvPath = $paths.AuditCsvPath
        manifestPath = $paths.ManifestPath
        ledgerPath = $paths.LedgerPath
    }

    Write-Host 'ALL GOVERNANCE CHECKS PASSED.'
    Write-Host "AuditCsv : $($paths.AuditCsvPath)"
    Write-Host "Manifest : $($paths.ManifestPath)"
    Write-Host "Ledger   : $($paths.LedgerPath)"
    Write-Host "Log      : $($paths.LogPath)"
    Write-Host "Evidence : $($paths.EvidenceDir)"
}

function Invoke-GovernanceHealthCheck {
    $paths = Get-GovernancePaths

    foreach ($path in @($paths.LedgerPath, $paths.LogPath, $paths.ManifestPath, $paths.AuditCsvPath)) {
        $directory = [System.IO.Path]::GetDirectoryName($path)
        if (-not (Test-Path -LiteralPath $directory)) {
            New-Item -ItemType Directory -Path $directory -Force | Out-Null
        }
    }

    if (-not (Test-Path -LiteralPath $paths.EvidenceDir)) {
        New-Item -ItemType Directory -Path $paths.EvidenceDir -Force | Out-Null
    }

    Write-GovernanceLog -Event 'health-check' -Data @{
        configPath = $script:ConfigPath
        repoRoot = $script:RepoRoot
    }

    Write-Host 'ALL GOVERNANCE CHECKS PASSED.'
    Write-Host "RepoRoot : $script:RepoRoot"
    Write-Host "Config   : $script:ConfigPath"
    Write-Host "Log      : $($paths.LogPath)"
}

function Invoke-GovernanceSelfTest {
    Invoke-GovernanceHealthCheck
    New-GovernanceAudit

    $paths = Get-GovernancePaths

    $required = @(
        $paths.LedgerPath,
        $paths.LogPath,
        $paths.ManifestPath,
        $paths.AuditCsvPath
    )

    foreach ($path in $required) {
        if (-not (Test-Path -LiteralPath $path)) {
            throw "Self-test failed. Missing artifact: $path"
        }
    }

    $manifest = Get-Content -LiteralPath $paths.ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $audit = Import-Csv -LiteralPath $paths.AuditCsvPath

    if ([int]$manifest.itemCount -ne @($audit).Count) {
        throw "Self-test failed. Manifest itemCount does not match audit CSV row count."
    }

    Write-GovernanceLog -Event 'self-test.complete' -Data @{
        itemCount = [int]$manifest.itemCount
    }

    Write-Host 'SELF TEST PASSED.'
}

function Register-GovernanceTask {
    $paths = Get-GovernancePaths
    Write-GovernanceLog -Event 'register-task.start' -Data @{
        taskName = $TaskName
        taskTime = $TaskTime
    }

    $argument = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" run"
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $argument
    $trigger = New-ScheduledTaskTrigger -Daily -At $TaskTime
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null

    Write-GovernanceLog -Event 'register-task.complete' -Data @{
        taskName = $TaskName
        taskTime = $TaskTime
        logPath = $paths.LogPath
    }

    Write-Host "Scheduled task registered: $TaskName at $TaskTime"
}

function Unregister-GovernanceTask {
    Write-GovernanceLog -Event 'unregister-task.start' -Data @{
        taskName = $TaskName
    }

    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-GovernanceLog -Event 'unregister-task.complete' -Data @{
            taskName = $TaskName
            removed = $true
        }
        Write-Host "Scheduled task removed: $TaskName"
    } else {
        Write-GovernanceLog -Event 'unregister-task.complete' -Data @{
            taskName = $TaskName
            removed = $false
        }
        Write-Host "Scheduled task not found: $TaskName"
    }
}

try {

function Get-ValidateArtifactPaths {
    $scriptRootVariable = Get-Variable -Name ScriptRoot -Scope Script -ErrorAction SilentlyContinue

    if ($scriptRootVariable -and -not [string]::IsNullOrWhiteSpace([string]$scriptRootVariable.Value)) {
        $repoRoot = Split-Path -Parent ([string]$scriptRootVariable.Value)
    }
    elseif (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
        $repoRoot = Split-Path -Parent $PSScriptRoot
    }
    else {
        $repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
    }

    [pscustomobject]@{
        RepoRoot     = $repoRoot
        ManifestPath = Join-Path $repoRoot 'out\governance-manifest.json'
        AuditCsvPath = Join-Path $repoRoot 'out\governance-audit.csv'
        LedgerPath   = Join-Path $repoRoot 'state\governance-ledger.jsonl'
        LogPath      = Join-Path $repoRoot 'logs\governance-log.jsonl'
        EvidencePath = Join-Path $repoRoot 'out\evidence'
    }
}

function Read-JsonLinesStrict {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $rows = @()
    $lineNo = 0

    foreach ($line in [System.IO.File]::ReadAllLines($Path)) {
        $lineNo++

        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        try {
            $rows += ($line | ConvertFrom-Json -ErrorAction Stop)
        }
        catch {
            throw ('{0} contains invalid JSON at line {1}: {2}' -f $Label, $lineNo, $Path)
        }
    }

    return ,$rows
}

function Get-ObjectPropertyValue {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string[]]$Names
    )

    foreach ($name in $Names) {
        $prop = $Object.PSObject.Properties[$name]
        if ($null -ne $prop) {
            return $prop.Value
        }
    }

    return $null
}

function Invoke-ValidateGovernance {
    $paths = Get-ValidateArtifactPaths

    foreach ($required in @(
        $paths.ManifestPath,
        $paths.AuditCsvPath,
        $paths.LedgerPath,
        $paths.LogPath
    )) {
        if (-not (Test-Path -LiteralPath $required)) {
            throw ('required artifact missing: {0}' -f $required)
        }
    }

    try {
        $manifest = [System.IO.File]::ReadAllText($paths.ManifestPath) | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        throw ('manifest is not valid JSON: {0}' -f $paths.ManifestPath)
    }

    $manifestItemCount = Get-ObjectPropertyValue -Object $manifest -Names @(
        'itemCount',
        'ItemCount',
        'itemsCount',
        'ItemsCount'
    )

    if ($null -eq $manifestItemCount) {
        throw ('manifest missing itemCount: {0}' -f $paths.ManifestPath)
    }

    $auditHeader = [System.IO.File]::ReadLines($paths.AuditCsvPath) | Select-Object -First 1
    if ([string]::IsNullOrWhiteSpace($auditHeader)) {
        throw ('audit csv is empty: {0}' -f $paths.AuditCsvPath)
    }

    $auditRows = @(Import-Csv -LiteralPath $paths.AuditCsvPath)
    $auditRowCount = $auditRows.Count

    if ([int]$manifestItemCount -ne [int]$auditRowCount) {
        throw ('itemCount mismatch: manifest={0} audit={1}' -f $manifestItemCount, $auditRowCount)
    }

    $pathColumns = @(
        'path',
        'Path',
        'relativePath',
        'RelativePath',
        'file',
        'File'
    )

    $hashColumns = @(
        'sha256',
        'Sha256',
        'SHA256',
        'hash',
        'Hash'
    )

    $seenPaths = New-Object 'System.Collections.Generic.HashSet[string]'

    foreach ($row in $auditRows) {
        $rowPath = Get-ObjectPropertyValue -Object $row -Names $pathColumns

        if ([string]::IsNullOrWhiteSpace([string]$rowPath)) {
            throw ('audit row missing path column value: {0}' -f $paths.AuditCsvPath)
        }

        if (-not $seenPaths.Add([string]$rowPath)) {
            throw ('duplicate audit path detected: {0}' -f $rowPath)
        }

        $rowHash = Get-ObjectPropertyValue -Object $row -Names $hashColumns

        if ($null -ne $rowHash -and -not [string]::IsNullOrWhiteSpace([string]$rowHash)) {
            if ([string]$rowHash -notmatch '^[0-9a-fA-F]{64}$') {
                throw ('invalid SHA-256 value in audit csv for path: {0}' -f $rowPath)
            }
        }
    }

    $ledgerRows = @(Read-JsonLinesStrict -Path $paths.LedgerPath -Label 'ledger')
    if ($ledgerRows.Count -eq 0) {
        throw ('ledger is empty: {0}' -f $paths.LedgerPath)
    }

    $logRows = @(Read-JsonLinesStrict -Path $paths.LogPath -Label 'log')
    if ($logRows.Count -eq 0) {
        throw ('log is empty: {0}' -f $paths.LogPath)
    }

    $latestLedgerRun = @(
        $ledgerRows |
            Where-Object {
                (Get-ObjectPropertyValue -Object $_ -Names @('event', 'Event')) -eq 'run'
            } |
            Select-Object -Last 1
    )

    if ($latestLedgerRun.Count -gt 0) {
        $ledgerItemCount = Get-ObjectPropertyValue -Object $latestLedgerRun[0] -Names @(
            'itemCount',
            'ItemCount',
            'itemsCount',
            'ItemsCount'
        )

        if ($null -ne $ledgerItemCount -and [int]$ledgerItemCount -ne [int]$manifestItemCount) {
            throw ('ledger latest run itemCount mismatch: ledger={0} manifest={1}' -f $ledgerItemCount, $manifestItemCount)
        }
    }

    $latestRunComplete = @(
        $logRows |
            Where-Object {
                (Get-ObjectPropertyValue -Object $_ -Names @('event', 'Event')) -eq 'run.complete'
            } |
            Select-Object -Last 1
    )

    if ($latestRunComplete.Count -gt 0) {
        $data = Get-ObjectPropertyValue -Object $latestRunComplete[0] -Names @('data', 'Data')

        if ($null -ne $data) {
            $logItemCount = Get-ObjectPropertyValue -Object $data -Names @(
                'itemCount',
                'ItemCount',
                'itemsCount',
                'ItemsCount'
            )

            if ($null -ne $logItemCount -and [int]$logItemCount -ne [int]$manifestItemCount) {
                throw ('log latest run.complete itemCount mismatch: log={0} manifest={1}' -f $logItemCount, $manifestItemCount)
            }
        }
    }

    if (Test-Path -LiteralPath $paths.EvidencePath) {
        if (-not (Get-Item -LiteralPath $paths.EvidencePath).PSIsContainer) {
            throw ('evidence path exists but is not a directory: {0}' -f $paths.EvidencePath)
        }
    }

    $logCommand = Get-Command Write-GovernanceLog -ErrorAction SilentlyContinue
    if ($logCommand) {
        Write-GovernanceLog -Level 'INFO' -Event 'validate.complete' -Data @{
            itemCount    = [int]$manifestItemCount
            auditCsvPath = $paths.AuditCsvPath
            manifestPath = $paths.ManifestPath
            ledgerPath   = $paths.LedgerPath
            logPath      = $paths.LogPath
        }
    }

    Write-Host 'VALIDATION PASSED.'

    [pscustomobject]@{
        RepoRoot      = $paths.RepoRoot
        Manifest      = $paths.ManifestPath
        AuditCsv      = $paths.AuditCsvPath
        Ledger        = $paths.LedgerPath
        Log           = $paths.LogPath
        Evidence      = $paths.EvidencePath
        ItemCount     = [int]$manifestItemCount
        AuditRows     = [int]$auditRowCount
        LogEntries    = $logRows.Count
        LedgerEntries = $ledgerRows.Count
    }
}

    switch ($Command) {
        'health-check' { Invoke-GovernanceHealthCheck }
        'run' { New-GovernanceAudit }
        'register-task' { Register-GovernanceTask }
        'unregister-task' { Unregister-GovernanceTask }
        'self-test' { Invoke-GovernanceSelfTest }
'validate' { Invoke-ValidateGovernance }
        default { throw "Unsupported command: $Command" }
    }
} catch {
    try {
        Write-GovernanceLog -Event 'error' -Level 'ERROR' -Data @{
            command = $Command
            message = $_.Exception.Message
            type = $_.Exception.GetType().FullName
        }
    } catch {
    }

    throw
}