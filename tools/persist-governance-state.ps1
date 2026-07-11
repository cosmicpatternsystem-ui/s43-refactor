[CmdletBinding()]
param(
    [string]$Branch = "main",
    [switch]$Push = $true,
    [switch]$TagRelease
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Run-Step {
    param(
        [string]$Title,
        [scriptblock]$Script
    )
    Write-Host ""
    Write-Host "==> $Title" -ForegroundColor Cyan
    & $Script
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
$stateJsonPath = Join-Path $outDir "governance-state.json"
$stateMdPath = Join-Path $docsDir "governance-state.md"
$validationLogPath = Join-Path $logsDir "persist-governance-validate.log"

Run-Step "Check current branch" {
    $currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
    if ($currentBranch -ne $Branch) {
        throw "Current branch is '$currentBranch' but expected '$Branch'"
    }
}

Run-Step "Run syntax check" {
    python -c "import ast, pathlib; ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); print('syntax: ok')"
}

Run-Step "Run governance validation" {
    $validateOutput = & python .\asoctl.py validate 2>&1
    $validateOutput | Tee-Object -FilePath $validationLogPath
    if ($LASTEXITCODE -ne 0) {
        throw "Governance validation failed"
    }
}

Run-Step "Collect repository facts" {
    $headCommit = (git rev-parse HEAD).Trim()
    $headShort = (git rev-parse --short HEAD).Trim()
    $statusShort = git status --short
    $isClean = [string]::IsNullOrWhiteSpace(($statusShort | Out-String))
    $remoteUrl = ""
    try {
        $remoteUrl = (git remote get-url origin).Trim()
    } catch {
        $remoteUrl = ""
    }

    $governanceDefs = python -c "import ast, pathlib, json; t=ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); out=[{'lineno':n.lineno,'end_lineno':getattr(n,'end_lineno',n.lineno)} for c in ast.walk(t) if isinstance(c,ast.ClassDef) and c.name=='ASOControl' for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='governance_validate']; print(json.dumps(out, ensure_ascii=True))"
    $governanceDefsObj = $governanceDefs | ConvertFrom-Json

    $artifacts = [ordered]@{
        manifest = Test-Path (Join-Path $outDir "governance-manifest.json")
        auditCsv = Test-Path (Join-Path $outDir "governance-audit.csv")
        ledger = Test-Path (Join-Path $stateDir "governance-ledger.jsonl")
        log = Test-Path (Join-Path $logsDir "governance-log.jsonl")
        evidenceDir = Test-Path (Join-Path $outDir "evidence")
    }

    $state = [ordered]@{
        generated_at_utc = $timestamp
        repo_root = $repoRoot
        branch = $Branch
        head_commit = $headCommit
        head_short = $headShort
        remote_origin = $remoteUrl
        working_tree_clean_before_persist = $isClean
        validation_command = "python .\asoctl.py validate"
        syntax_command = "python -c `"import ast, pathlib; ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); print('syntax: ok')`""
        asoctl_path = "asoctl.py"
        governance_validate_definitions = $governanceDefsObj
        governance_validate_definition_count = @($governanceDefsObj).Count
        artifacts = $artifacts
    }

    [System.IO.File]::WriteAllText($stateJsonPath, ($state | ConvertTo-Json -Depth 6), [System.Text.UTF8Encoding]::new($false))

    $md = @"
# Governance State

Generated at: $timestamp

## Durable Facts
- Branch: $Branch
- HEAD: $headShort ($headCommit)
- Working tree clean before persist step: $isClean
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

## Source of Truth
This file is generated from the repository state, git metadata, and command output.
It does not rely on chat memory.
"@

    $md = $md -replace "`r?`n", "`n"
    [System.IO.File]::WriteAllText($stateMdPath, $md, [System.Text.UTF8Encoding]::new($false))
}

Run-Step "Stage persistent state files" {
    git add -- tools/persist-governance-state.ps1 docs/governance-state.md out/governance-state.json logs/persist-governance-validate.log
}

Run-Step "Commit if needed" {
    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "No staged changes to commit."
    } else {
        git commit -m "docs(governance): persist verified repository state"
    }
}

if ($TagRelease) {
    Run-Step "Create tag" {
        $tagName = "governance-state-" + (Get-Date -Format "yyyyMMdd-HHmmss")
        git tag $tagName
        Write-Host "Created tag: $tagName"
    }
}

if ($Push) {
    Run-Step "Push branch if origin exists" {
        try {
            $null = (git remote get-url origin).Trim()
            git push origin $Branch
            if ($TagRelease) {
                git push origin --tags
            }
        } catch {
            Write-Host "No origin remote configured; skipping push." -ForegroundColor Yellow
        }
    }
}

Run-Step "Final status" {
    git status --short
    git log -1 --oneline
}

Write-Host ""
Write-Host "Persistence workflow completed." -ForegroundColor Green