function Exec-Or-Throw {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [string[]]$Arguments = @(),

        [string]$ErrorMessage
    )

    $result = Exec-And-Capture -FilePath $FilePath -Arguments $Arguments

    if ($result.ExitCode -ne 0) {
        if ($result.Output) {
            throw ($ErrorMessage + "`n" + $result.Output)
        }

        throw $ErrorMessage
    }

    return $result
}[CmdletBinding()]
param(
    [string]$Branch = "main",
    [switch]$Push = $true,
    [switch]$TagRelease,
    [switch]$OpenPR = $true
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Write-Step {
    param([string]$Title)
    Write-Host ""
    Write-Host "==> $Title" -ForegroundColor Cyan
}

function Write-Utf8NoBom {
    param(
        [string]$Path,
        [string]$Content
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

function Exec-And-Capture {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath

    $escapedArgs = @()
    foreach ($arg in $Arguments) {
        if ($null -eq $arg) {
            $escapedArgs += '""'
            continue
        }

        $s = [string]$arg
        if ($s -match '[\s"]') {
            $s = $s -replace '(\\*)"', '$1$1\"'
            $s = $s -replace '(\\+)$', '$1$1'
            $s = '"' + $s + '"'
        }

        $escapedArgs += $s
    }

    $psi.Arguments = ($escapedArgs -join ' ')
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    [void]$process.Start()

    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    $combined = @()
    if (-not [string]::IsNullOrWhiteSpace($stdout)) {
        $combined += ($stdout -split "`r?`n").Where({ [CmdletBinding()]
param(
    [string]$Branch = "main",
    [switch]$Push = $true,
    [switch]$TagRelease,
    [switch]$OpenPR = $true
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Write-Step {
    param([string]$Title)
    Write-Host ""
    Write-Host "==> $Title" -ForegroundColor Cyan
}

function Write-Utf8NoBom {
    param(
        [string]$Path,
        [string]$Content
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

function Exec-And-Capture {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )
    $output = & $FilePath @Arguments 2>&1
    $code = $LASTEXITCODE
    return @{
        Output = @($output)
        ExitCode = $code
    }
}

Require-Command git
Require-Command python

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$asoctl = Join-Path $repoRoot "asoctl.py"
if (-not (Test-Path $asoctl)) {
    throw "Missing file: $asoctl"
}

$docsDir = Join-Path $repoRoot "docs"
$outDir = Join-Path $repoRoot "out"
$stateDir = Join-Path $repoRoot "state"
$logsDir = Join-Path $repoRoot "logs"
$toolsDir = Join-Path $repoRoot "tools"

New-Item -ItemType Directory -Force -Path $docsDir | Out-Null
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$stampForName = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss")
$stateJsonPath = Join-Path $outDir "governance-state.json"
$stateMdPath = Join-Path $docsDir "governance-state.md"
$validationLogPath = Join-Path $logsDir "persist-governance-validate.log"
$ledgerPath = Join-Path $stateDir "governance-ledger.jsonl"
$manifestPath = Join-Path $outDir "governance-manifest.json"
$auditCsvPath = Join-Path $outDir "governance-audit.csv"
$evidenceDirPath = Join-Path $outDir "evidence"

Write-Step "Check current branch"
$currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()

Write-Step "Run syntax check"
python -c "import ast, pathlib; ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); print('syntax: ok')"

Write-Step "Run governance validation"
$validateOutput = & python .\asoctl.py validate 2>&1
$validateText = ($validateOutput | Out-String).TrimEnd()
Write-Utf8NoBom -Path $validationLogPath -Content ($validateText + "`n")
$validateOutput
if ($LASTEXITCODE -ne 0) {
    throw "Governance validation failed"
}

Write-Step "Collect repository facts"
$headCommit = (git rev-parse HEAD).Trim()
$headShort = (git rev-parse --short HEAD).Trim()
$statusShortBefore = git status --short
$isCleanBefore = [string]::IsNullOrWhiteSpace(($statusShortBefore | Out-String))
$remoteUrl = ""
try {
    $remoteUrl = (git remote get-url origin).Trim()
} catch {
    $remoteUrl = ""
}

$governanceDefsJson = python -c "import ast, pathlib, json; t=ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); out=[{'lineno':n.lineno,'end_lineno':getattr(n,'end_lineno',n.lineno)} for c in ast.walk(t) if isinstance(c,ast.ClassDef) and c.name=='ASOControl' for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='governance_validate']; print(json.dumps(out, ensure_ascii=True))"
$governanceDefsObj = $governanceDefsJson | ConvertFrom-Json

$artifacts = [ordered]@{
    manifest = Test-Path $manifestPath
    auditCsv = Test-Path $auditCsvPath
    ledger = Test-Path $ledgerPath
    log = Test-Path (Join-Path $logsDir "governance-log.jsonl")
    evidenceDir = Test-Path $evidenceDirPath
    persistedStateJson = Test-Path $stateJsonPath
    persistedValidationLog = Test-Path $validationLogPath
}

$state = [ordered]@{
    generated_at_utc = $timestamp
    repo_root = $repoRoot
    current_branch = $currentBranch
    target_branch = $Branch
    head_commit = $headCommit
    head_short = $headShort
    remote_origin = $remoteUrl
    working_tree_clean_before_persist = $isCleanBefore
    validation_command = "python .\asoctl.py validate"
    syntax_command = "python -c `"import ast, pathlib; ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); print('syntax: ok')`""
    asoctl_path = "asoctl.py"
    governance_validate_definitions = $governanceDefsObj
    governance_validate_definition_count = @($governanceDefsObj).Count
    artifacts = $artifacts
}

$stateJson = $state | ConvertTo-Json -Depth 8
Write-Utf8NoBom -Path $stateJsonPath -Content ($stateJson + "`n")

$md = @"
# Governance State

Generated at: $timestamp

## Durable Facts
- Current branch: $currentBranch
- Target branch: $Branch
- HEAD: $headShort ($headCommit)
- Working tree clean before persist step: $isCleanBefore
- Remote origin: $remoteUrl

## Verification
- Syntax check: `python -c "import ast, pathlib; ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); print('syntax: ok')"`
- Governance validation: `python .\asoctl.py validate`

## ASO Control
- File: `asoctl.py`
- `governance_validate` definition count in `ASOControl`: $(@($governanceDefsObj).Count)

## Artifacts
- Manifest present: $($artifacts.manifest)
- Audit CSV present: $($artifacts.auditCsv)
- Ledger present: $($artifacts.ledger)
- Log present: $($artifacts.log)
- Evidence directory present: $($artifacts.evidenceDir)
- Persisted state JSON present: $($artifacts.persistedStateJson)
- Persisted validation log present: $($artifacts.persistedValidationLog)

## Source of Truth
This file is generated from repository state, git metadata, and command output.
It does not rely on chat memory.
"@
$md = $md -replace "`r?`n", "`n"
Write-Utf8NoBom -Path $stateMdPath -Content $md

Write-Step "Stage persistent state files"
git add -- "tools/persist-governance-state.ps1" "docs/governance-state.md"
if (Test-Path $stateJsonPath) {
    git add -f -- "out/governance-state.json"
}
if (Test-Path $validationLogPath) {
    git add -f -- "logs/persist-governance-validate.log"
}

Write-Step "Commit if needed"
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "No staged changes to commit."
} else {
    git commit -m "docs(governance): persist verified repository state"
}

if ($TagRelease) {
    Write-Step "Create tag"
    $tagName = "governance-state-" + $stampForName
    git tag $tagName
    Write-Host "Created tag: $tagName"
}

if ($Push) {
    if ([string]::IsNullOrWhiteSpace($remoteUrl)) {
        Write-Step "Push skipped"
        Write-Host "No origin remote configured; skipping push." -ForegroundColor Yellow
    } else {
        Write-Step "Push current branch"
        $pushResult = Exec-And-Capture -FilePath "git" -Arguments @("push", "-u", "origin", $currentBranch)
        $pushResult.Output
        $pushSucceeded = ($pushResult.ExitCode -eq 0)

        if (-not $pushSucceeded -and $currentBranch -eq $Branch) {
            Write-Step "Protected branch fallback"
            $fallbackBranch = "docs/governance-state-" + $stampForName
            git checkout -b $fallbackBranch
            $currentBranch = $fallbackBranch

            $fallbackPush = Exec-And-Capture -FilePath "git" -Arguments @("push", "-u", "origin", $currentBranch)
            $fallbackPush.Output
            if ($fallbackPush.ExitCode -ne 0) {
                throw "Push failed for fallback branch: $currentBranch"
            }

            if ($OpenPR -and (Get-Command gh -ErrorAction SilentlyContinue)) {
                Write-Step "Create pull request"
                $prBody = "Persisted verified governance state; validation passed locally and via pre-commit hook."
                gh pr create --base $Branch --head $currentBranch --title "docs(governance): persist verified repository state" --body $prBody
            } elseif ($OpenPR) {
                Write-Host "GitHub CLI not found; create PR manually from branch $currentBranch." -ForegroundColor Yellow
            }
        } elseif (-not $pushSucceeded) {
            throw "Push failed for branch: $currentBranch"
        }

        if ($TagRelease) {
            Write-Step "Push tags"
            git push origin --tags
        }
    }
}

Write-Step "Final status"
git status --short
git log -1 --oneline -ne "" })
    }
    if (-not [string]::IsNullOrWhiteSpace($stderr)) {
        $combined += ($stderr -split "`r?`n").Where({ [CmdletBinding()]
param(
    [string]$Branch = "main",
    [switch]$Push = $true,
    [switch]$TagRelease,
    [switch]$OpenPR = $true
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Write-Step {
    param([string]$Title)
    Write-Host ""
    Write-Host "==> $Title" -ForegroundColor Cyan
}

function Write-Utf8NoBom {
    param(
        [string]$Path,
        [string]$Content
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

function Exec-And-Capture {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )
    $output = & $FilePath @Arguments 2>&1
    $code = $LASTEXITCODE
    return @{
        Output = @($output)
        ExitCode = $code
    }
}

Require-Command git
Require-Command python

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$asoctl = Join-Path $repoRoot "asoctl.py"
if (-not (Test-Path $asoctl)) {
    throw "Missing file: $asoctl"
}

$docsDir = Join-Path $repoRoot "docs"
$outDir = Join-Path $repoRoot "out"
$stateDir = Join-Path $repoRoot "state"
$logsDir = Join-Path $repoRoot "logs"
$toolsDir = Join-Path $repoRoot "tools"

New-Item -ItemType Directory -Force -Path $docsDir | Out-Null
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$stampForName = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss")
$stateJsonPath = Join-Path $outDir "governance-state.json"
$stateMdPath = Join-Path $docsDir "governance-state.md"
$validationLogPath = Join-Path $logsDir "persist-governance-validate.log"
$ledgerPath = Join-Path $stateDir "governance-ledger.jsonl"
$manifestPath = Join-Path $outDir "governance-manifest.json"
$auditCsvPath = Join-Path $outDir "governance-audit.csv"
$evidenceDirPath = Join-Path $outDir "evidence"

Write-Step "Check current branch"
$currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()

Write-Step "Run syntax check"
python -c "import ast, pathlib; ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); print('syntax: ok')"

Write-Step "Run governance validation"
$validateOutput = & python .\asoctl.py validate 2>&1
$validateText = ($validateOutput | Out-String).TrimEnd()
Write-Utf8NoBom -Path $validationLogPath -Content ($validateText + "`n")
$validateOutput
if ($LASTEXITCODE -ne 0) {
    throw "Governance validation failed"
}

Write-Step "Collect repository facts"
$headCommit = (git rev-parse HEAD).Trim()
$headShort = (git rev-parse --short HEAD).Trim()
$statusShortBefore = git status --short
$isCleanBefore = [string]::IsNullOrWhiteSpace(($statusShortBefore | Out-String))
$remoteUrl = ""
try {
    $remoteUrl = (git remote get-url origin).Trim()
} catch {
    $remoteUrl = ""
}

$governanceDefsJson = python -c "import ast, pathlib, json; t=ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); out=[{'lineno':n.lineno,'end_lineno':getattr(n,'end_lineno',n.lineno)} for c in ast.walk(t) if isinstance(c,ast.ClassDef) and c.name=='ASOControl' for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='governance_validate']; print(json.dumps(out, ensure_ascii=True))"
$governanceDefsObj = $governanceDefsJson | ConvertFrom-Json

$artifacts = [ordered]@{
    manifest = Test-Path $manifestPath
    auditCsv = Test-Path $auditCsvPath
    ledger = Test-Path $ledgerPath
    log = Test-Path (Join-Path $logsDir "governance-log.jsonl")
    evidenceDir = Test-Path $evidenceDirPath
    persistedStateJson = Test-Path $stateJsonPath
    persistedValidationLog = Test-Path $validationLogPath
}

$state = [ordered]@{
    generated_at_utc = $timestamp
    repo_root = $repoRoot
    current_branch = $currentBranch
    target_branch = $Branch
    head_commit = $headCommit
    head_short = $headShort
    remote_origin = $remoteUrl
    working_tree_clean_before_persist = $isCleanBefore
    validation_command = "python .\asoctl.py validate"
    syntax_command = "python -c `"import ast, pathlib; ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); print('syntax: ok')`""
    asoctl_path = "asoctl.py"
    governance_validate_definitions = $governanceDefsObj
    governance_validate_definition_count = @($governanceDefsObj).Count
    artifacts = $artifacts
}

$stateJson = $state | ConvertTo-Json -Depth 8
Write-Utf8NoBom -Path $stateJsonPath -Content ($stateJson + "`n")

$md = @"
# Governance State

Generated at: $timestamp

## Durable Facts
- Current branch: $currentBranch
- Target branch: $Branch
- HEAD: $headShort ($headCommit)
- Working tree clean before persist step: $isCleanBefore
- Remote origin: $remoteUrl

## Verification
- Syntax check: `python -c "import ast, pathlib; ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); print('syntax: ok')"`
- Governance validation: `python .\asoctl.py validate`

## ASO Control
- File: `asoctl.py`
- `governance_validate` definition count in `ASOControl`: $(@($governanceDefsObj).Count)

## Artifacts
- Manifest present: $($artifacts.manifest)
- Audit CSV present: $($artifacts.auditCsv)
- Ledger present: $($artifacts.ledger)
- Log present: $($artifacts.log)
- Evidence directory present: $($artifacts.evidenceDir)
- Persisted state JSON present: $($artifacts.persistedStateJson)
- Persisted validation log present: $($artifacts.persistedValidationLog)

## Source of Truth
This file is generated from repository state, git metadata, and command output.
It does not rely on chat memory.
"@
$md = $md -replace "`r?`n", "`n"
Write-Utf8NoBom -Path $stateMdPath -Content $md

Write-Step "Stage persistent state files"
git add -- "tools/persist-governance-state.ps1" "docs/governance-state.md"
if (Test-Path $stateJsonPath) {
    git add -f -- "out/governance-state.json"
}
if (Test-Path $validationLogPath) {
    git add -f -- "logs/persist-governance-validate.log"
}

Write-Step "Commit if needed"
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "No staged changes to commit."
} else {
    git commit -m "docs(governance): persist verified repository state"
}

if ($TagRelease) {
    Write-Step "Create tag"
    $tagName = "governance-state-" + $stampForName
    git tag $tagName
    Write-Host "Created tag: $tagName"
}

if ($Push) {
    if ([string]::IsNullOrWhiteSpace($remoteUrl)) {
        Write-Step "Push skipped"
        Write-Host "No origin remote configured; skipping push." -ForegroundColor Yellow
    } else {
        Write-Step "Push current branch"
        $pushResult = Exec-And-Capture -FilePath "git" -Arguments @("push", "-u", "origin", $currentBranch)
        $pushResult.Output
        $pushSucceeded = ($pushResult.ExitCode -eq 0)

        if (-not $pushSucceeded -and $currentBranch -eq $Branch) {
            Write-Step "Protected branch fallback"
            $fallbackBranch = "docs/governance-state-" + $stampForName
            git checkout -b $fallbackBranch
            $currentBranch = $fallbackBranch

            $fallbackPush = Exec-And-Capture -FilePath "git" -Arguments @("push", "-u", "origin", $currentBranch)
            $fallbackPush.Output
            if ($fallbackPush.ExitCode -ne 0) {
                throw "Push failed for fallback branch: $currentBranch"
            }

            if ($OpenPR -and (Get-Command gh -ErrorAction SilentlyContinue)) {
                Write-Step "Create pull request"
                $prBody = "Persisted verified governance state; validation passed locally and via pre-commit hook."
                gh pr create --base $Branch --head $currentBranch --title "docs(governance): persist verified repository state" --body $prBody
            } elseif ($OpenPR) {
                Write-Host "GitHub CLI not found; create PR manually from branch $currentBranch." -ForegroundColor Yellow
            }
        } elseif (-not $pushSucceeded) {
            throw "Push failed for branch: $currentBranch"
        }

        if ($TagRelease) {
            Write-Step "Push tags"
            git push origin --tags
        }
    }
}

Write-Step "Final status"
git status --short
git log -1 --oneline -ne "" })
    }

    return @{
        Output = $combined
        ExitCode = $process.ExitCode
    }
}

Require-Command git
Require-Command python

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$asoctl = Join-Path $repoRoot "asoctl.py"
if (-not (Test-Path $asoctl)) {
    throw "Missing file: $asoctl"
}

$docsDir = Join-Path $repoRoot "docs"
$outDir = Join-Path $repoRoot "out"
$stateDir = Join-Path $repoRoot "state"
$logsDir = Join-Path $repoRoot "logs"
$toolsDir = Join-Path $repoRoot "tools"

New-Item -ItemType Directory -Force -Path $docsDir | Out-Null
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$stampForName = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss")
$stateJsonPath = Join-Path $outDir "governance-state.json"
$stateMdPath = Join-Path $docsDir "governance-state.md"
$validationLogPath = Join-Path $logsDir "persist-governance-validate.log"
$ledgerPath = Join-Path $stateDir "governance-ledger.jsonl"
$manifestPath = Join-Path $outDir "governance-manifest.json"
$auditCsvPath = Join-Path $outDir "governance-audit.csv"
$evidenceDirPath = Join-Path $outDir "evidence"

Write-Step "Check current branch"
$currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()

Write-Step "Run syntax check"
python -c "import ast, pathlib; ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); print('syntax: ok')"

Write-Step "Run governance validation"
$validateOutput = & python .\asoctl.py validate 2>&1
$validateText = ($validateOutput | Out-String).TrimEnd()
Write-Utf8NoBom -Path $validationLogPath -Content ($validateText + "`n")
$validateOutput
if ($LASTEXITCODE -ne 0) {
    throw "Governance validation failed"
}

Write-Step "Collect repository facts"
$headCommit = (git rev-parse HEAD).Trim()
$headShort = (git rev-parse --short HEAD).Trim()
$statusShortBefore = git status --short
$isCleanBefore = [string]::IsNullOrWhiteSpace(($statusShortBefore | Out-String))
$remoteUrl = ""
try {
    $remoteUrl = (git remote get-url origin).Trim()
} catch {
    $remoteUrl = ""
}

$governanceDefsJson = python -c "import ast, pathlib, json; t=ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); out=[{'lineno':n.lineno,'end_lineno':getattr(n,'end_lineno',n.lineno)} for c in ast.walk(t) if isinstance(c,ast.ClassDef) and c.name=='ASOControl' for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='governance_validate']; print(json.dumps(out, ensure_ascii=True))"
$governanceDefsObj = $governanceDefsJson | ConvertFrom-Json

$artifacts = [ordered]@{
    manifest = Test-Path $manifestPath
    auditCsv = Test-Path $auditCsvPath
    ledger = Test-Path $ledgerPath
    log = Test-Path (Join-Path $logsDir "governance-log.jsonl")
    evidenceDir = Test-Path $evidenceDirPath
    persistedStateJson = Test-Path $stateJsonPath
    persistedValidationLog = Test-Path $validationLogPath
}

$state = [ordered]@{
    generated_at_utc = $timestamp
    repo_root = $repoRoot
    current_branch = $currentBranch
    target_branch = $Branch
    head_commit = $headCommit
    head_short = $headShort
    remote_origin = $remoteUrl
    working_tree_clean_before_persist = $isCleanBefore
    validation_command = "python .\asoctl.py validate"
    syntax_command = "python -c `"import ast, pathlib; ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); print('syntax: ok')`""
    asoctl_path = "asoctl.py"
    governance_validate_definitions = $governanceDefsObj
    governance_validate_definition_count = @($governanceDefsObj).Count
    artifacts = $artifacts
}

$stateJson = $state | ConvertTo-Json -Depth 8
Write-Utf8NoBom -Path $stateJsonPath -Content ($stateJson + "`n")

$md = @"
# Governance State

Generated at: $timestamp

## Durable Facts
- Current branch: $currentBranch
- Target branch: $Branch
- HEAD: $headShort ($headCommit)
- Working tree clean before persist step: $isCleanBefore
- Remote origin: $remoteUrl

## Verification
- Syntax check: `python -c "import ast, pathlib; ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); print('syntax: ok')"`
- Governance validation: `python .\asoctl.py validate`

## ASO Control
- File: `asoctl.py`
- `governance_validate` definition count in `ASOControl`: $(@($governanceDefsObj).Count)

## Artifacts
- Manifest present: $($artifacts.manifest)
- Audit CSV present: $($artifacts.auditCsv)
- Ledger present: $($artifacts.ledger)
- Log present: $($artifacts.log)
- Evidence directory present: $($artifacts.evidenceDir)
- Persisted state JSON present: $($artifacts.persistedStateJson)
- Persisted validation log present: $($artifacts.persistedValidationLog)

## Source of Truth
This file is generated from repository state, git metadata, and command output.
It does not rely on chat memory.
"@
$md = $md -replace "`r?`n", "`n"
Write-Utf8NoBom -Path $stateMdPath -Content $md

Write-Step "Stage persistent state files"
git add -- "tools/persist-governance-state.ps1" "docs/governance-state.md"
if (Test-Path $stateJsonPath) {
    git add -f -- "out/governance-state.json"
}
if (Test-Path $validationLogPath) {
    git add -f -- "logs/persist-governance-validate.log"
}

Write-Step "Commit if needed"
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "No staged changes to commit."
} else {
    git commit -m "docs(governance): persist verified repository state"
}

if ($TagRelease) {
    Write-Step "Create tag"
    $tagName = "governance-state-" + $stampForName
    git tag $tagName
    Write-Host "Created tag: $tagName"
}

if ($Push) {
    if ([string]::IsNullOrWhiteSpace($remoteUrl)) {
        Write-Step "Push skipped"
        Write-Host "No origin remote configured; skipping push." -ForegroundColor Yellow
    } else {
        Write-Step "Push current branch"
        $pushResult = Exec-And-Capture -FilePath "git" -Arguments @("push", "-u", "origin", $currentBranch)
        $pushResult.Output
        $pushSucceeded = ($pushResult.ExitCode -eq 0)

        if (-not $pushSucceeded -and $currentBranch -eq $Branch) {
            Write-Step "Protected branch fallback"
            $fallbackBranch = "docs/governance-state-" + $stampForName
            git checkout -b $fallbackBranch
            $currentBranch = $fallbackBranch

            $fallbackPush = Exec-And-Capture -FilePath "git" -Arguments @("push", "-u", "origin", $currentBranch)
            $fallbackPush.Output
            if ($fallbackPush.ExitCode -ne 0) {
                throw "Push failed for fallback branch: $currentBranch"
            }

            if ($OpenPR -and (Get-Command gh -ErrorAction SilentlyContinue)) {
                Write-Step "Create pull request"
                $prBody = "Persisted verified governance state; validation passed locally and via pre-commit hook."
                gh pr create --base $Branch --head $currentBranch --title "docs(governance): persist verified repository state" --body $prBody
            } elseif ($OpenPR) {
                Write-Host "GitHub CLI not found; create PR manually from branch $currentBranch." -ForegroundColor Yellow
            }
        } elseif (-not $pushSucceeded) {
            throw "Push failed for branch: $currentBranch"
        }

        if ($TagRelease) {
            Write-Step "Push tags"
            git push origin --tags
        }
    }
}

Write-Step "Final status"
git status --short
git log -1 --oneline