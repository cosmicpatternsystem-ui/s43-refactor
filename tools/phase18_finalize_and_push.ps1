[CmdletBinding()]
param(
    [string]$Message = "",
    [string]$Branch = "",
    [string]$ApprovalToken = "APPROVE_PHASE18",
    [switch]$AutoApprove
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Fail {
    param([string]$Text)
    throw $Text
}

function Info {
    param([string]$Text)
    Write-Host $Text
}

function Assert-CommandExists {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Fail ('Required command not found: ' + $Name)
    }
}

function Invoke-GitLines {
    param(
        [string]$RepoRoot,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    $output = & git -C $RepoRoot @Args
    if ($LASTEXITCODE -ne 0) {
        Fail ('git command failed: git -C "' + $RepoRoot + '" ' + ($Args -join ' '))
    }
    return @($output)
}

function Invoke-GitText {
    param(
        [string]$RepoRoot,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    $lines = Invoke-GitLines -RepoRoot $RepoRoot @Args
    return (($lines -join "`n").Trim())
}

function Exec-Git {
    param(
        [string]$RepoRoot,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    & git -C $RepoRoot @Args
    if ($LASTEXITCODE -ne 0) {
        Fail ('git command failed: git -C "' + $RepoRoot + '" ' + ($Args -join ' '))
    }
}

function Get-RepoRoot {
    $current = (Get-Location).ProviderPath

    try {
        $probe = & git -C $current rev-parse --show-toplevel 2>$null
        if ($probe) {
            $joined = ($probe -join "`n").Trim()
            if ((-not [string]::IsNullOrWhiteSpace($joined)) -and (Test-Path -LiteralPath $joined)) {
                return $joined
            }
        }
    }
    catch {
    }

    try {
        & git -C $current rev-parse --is-inside-work-tree 1>$null 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $current
        }
    }
    catch {
    }

    Fail 'Could not determine repository root from current directory.'
}

function Get-CurrentBranch {
    param([string]$RepoRoot)

    $b = Invoke-GitText -RepoRoot $RepoRoot -Args @('rev-parse','--abbrev-ref','HEAD')
    if ([string]::IsNullOrWhiteSpace($b)) {
        Fail 'Could not determine current git branch.'
    }
    return $b
}

function Get-UpstreamRefOrNull {
    param([string]$RepoRoot)

    try {
        $u = Invoke-GitText -RepoRoot $RepoRoot -Args @('rev-parse','--abbrev-ref','--symbolic-full-name','@{u}')
        if ([string]::IsNullOrWhiteSpace($u)) {
            return $null
        }
        return $u
    }
    catch {
        return $null
    }
}

function Normalize-RepoRelativePath {
    param(
        [string]$RepoRoot,
        [string]$PathText
    )

    $full = $PathText
    if (-not [System.IO.Path]::IsPathRooted($full)) {
        $full = Join-Path $RepoRoot $PathText
    }

    $fullResolved = [System.IO.Path]::GetFullPath($full)
    $rootResolved = [System.IO.Path]::GetFullPath($RepoRoot)

    if ($fullResolved.StartsWith($rootResolved, [System.StringComparison]::OrdinalIgnoreCase)) {
        $rel = $fullResolved.Substring($rootResolved.Length).TrimStart('\','/')
    }
    else {
        $rel = $PathText
    }

    return ($rel -replace '\\','/')
}

function Get-TrackedModifiedPaths {
    param([string]$RepoRoot)

    $lines = @(Invoke-GitLines -RepoRoot $RepoRoot -Args @('status','--porcelain'))
    $result = New-Object 'System.Collections.Generic.List[string]'

    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        if ($line.StartsWith('?? ')) {
            $p = $line.Substring(3).Trim()
            $result.Add(($p -replace '\\','/'))
            continue
        }

        if ($line.Length -ge 4) {
            $p = $line.Substring(3).Trim()
            $result.Add(($p -replace '\\','/'))
        }
    }

    return @($result | Sort-Object -Unique)
}

function Test-PathSetEqual {
    param(
        [string[]]$Actual,
        [string[]]$Expected
    )

    $a = @($Actual | Sort-Object -Unique)
    $e = @($Expected | Sort-Object -Unique)

    if ($a.Count -ne $e.Count) {
        return $false
    }

    for ($i = 0; $i -lt $a.Count; $i++) {
        if ($a[$i] -cne $e[$i]) {
            return $false
        }
    }

    return $true
}

function Get-Phase18ApprovedPaths {
    param([string]$RepoRoot)

    $candidates = @(
        (Join-Path $RepoRoot 'audit'),
        (Join-Path $RepoRoot 'audits'),
        (Join-Path $RepoRoot 'artifacts'),
        (Join-Path $RepoRoot 'evidence'),
        (Join-Path $RepoRoot 'logs'),
        (Join-Path $RepoRoot 'tools\audit'),
        (Join-Path $RepoRoot 'tools\audits'),
        (Join-Path $RepoRoot 'tools\artifacts'),
        (Join-Path $RepoRoot 'tools\evidence'),
        (Join-Path $RepoRoot 'tools\logs')
    )

    $auditRoot = $null

    foreach ($dir in $candidates) {
        if ((Test-Path -LiteralPath $dir) -and (Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue | Select-Object -First 1)) {
            $auditRoot = $dir
            break
        }
    }

    if ($null -eq $auditRoot) {
        Fail 'Could not find any non-empty audit/evidence directory.'
    }

    Info ('AUDIT_DIR: ' + $auditRoot)

    $files = Get-ChildItem -LiteralPath $auditRoot -File -ErrorAction Stop | Sort-Object Name
    if (($null -eq $files) -or ($files.Count -eq 0)) {
        Fail ('Audit directory is empty: ' + $auditRoot)
    }

    $approved = New-Object 'System.Collections.Generic.List[string]'
    foreach ($f in $files) {
        $approved.Add((Normalize-RepoRelativePath -RepoRoot $RepoRoot -PathText $f.FullName))
    }

    return @($approved | Sort-Object -Unique)
}

function Assert-ApprovedPathsExist {
    param(
        [string]$RepoRoot,
        [string[]]$Paths
    )

    foreach ($p in $Paths) {
        $full = Join-Path $RepoRoot ($p -replace '/', '\')
        if (-not (Test-Path -LiteralPath $full)) {
            Fail ('Approved path missing on disk: ' + $p)
        }
    }
}

function Confirm-FinalApproval {
    param(
        [string]$Token,
        [switch]$Bypass
    )

    if ($Bypass) {
        Info 'FINAL APPROVAL: AUTO-APPROVED'
        return
    }

    Info ''
    Info 'FINAL APPROVAL REQUIRED'
    Info ('Type exactly: ' + $Token)
    $entered = Read-Host 'Approval'

    if ($entered -cne $Token) {
        Fail 'Final approval token mismatch. Aborting.'
    }

    Info 'FINAL APPROVAL ACCEPTED'
}

Assert-CommandExists -Name 'git'

$repoRoot = Get-RepoRoot

if ([string]::IsNullOrWhiteSpace($Branch)) {
    $Branch = Get-CurrentBranch -RepoRoot $repoRoot
}

$upstream = Get-UpstreamRefOrNull -RepoRoot $repoRoot
if ($null -eq $upstream) {
    Info ('No upstream configured. Push will use: origin ' + $Branch)
}
else {
    Info ('Detected upstream: ' + $upstream)
}

if ([string]::IsNullOrWhiteSpace($Message)) {
    $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
    $Message = 'audit: finalize approved phase18 evidence ' + $ts
}

$approvedPaths = Get-Phase18ApprovedPaths -RepoRoot $repoRoot

if (($null -eq $approvedPaths) -or ($approvedPaths.Count -eq 0)) {
    Fail 'Approved paths list is empty.'
}

Info ('APPROVED_PATHS_COUNT: ' + $approvedPaths.Count)
foreach ($p in $approvedPaths) {
    Info ('APPROVED: ' + $p)
}

Assert-ApprovedPathsExist -RepoRoot $repoRoot -Paths $approvedPaths

$dirtyBefore = Get-TrackedModifiedPaths -RepoRoot $repoRoot

if (-not (Test-PathSetEqual -Actual $dirtyBefore -Expected $approvedPaths)) {
    Info 'DIRTY PATHS DETECTED:'
    foreach ($d in ($dirtyBefore | Sort-Object -Unique)) {
        Info ('DIRTY: ' + $d)
    }
    Fail 'Working tree contains changes outside approved paths, or approved paths do not exactly match current dirty set.'
}

Exec-Git -RepoRoot $repoRoot -Args @('diff','--check')
Info 'PHASE18_VERIFY_OK'

Confirm-FinalApproval -Token $ApprovalToken -Bypass:$AutoApprove

Exec-Git -RepoRoot $repoRoot -Args @('add','--') + $approvedPaths
Info 'FINALIZE_STAGE_OK'

$staged = @(Invoke-GitLines -RepoRoot $repoRoot -Args @('diff','--cached','--name-only'))
$staged = @($staged | ForEach-Object { $_ -replace '\\','/' } | Sort-Object -Unique)

if (-not (Test-PathSetEqual -Actual $staged -Expected $approvedPaths)) {
    Info 'STAGED PATHS:'
    foreach ($s in $staged) {
        Info ('STAGED: ' + $s)
    }
    Fail 'Staged paths do not exactly match approved paths.'
}

Exec-Git -RepoRoot $repoRoot -Args @('commit','-m',$Message)
Info 'FINALIZE_COMMIT_OK'

if (($null -ne $upstream) -and $upstream.Contains('/')) {
    Exec-Git -RepoRoot $repoRoot -Args @('push')
}
else {
    Exec-Git -RepoRoot $repoRoot -Args @('push','origin',$Branch)
}

Info 'FINALIZE_PUSH_OK'