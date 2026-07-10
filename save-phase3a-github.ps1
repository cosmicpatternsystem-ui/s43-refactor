param(
    [string]$RepoRoot = "G:\s43_work\s43_g11_work",

    [string]$CanonicalPath = ".\asox-autopilot-phase3a.ps1",
    [string]$RepairPath = ".\repair-phase3a-complete.ps1",
    [string]$TargetPath = ".\run-phase3a-repair.ps1",
    [string]$CollectorPath = ".\collect-phase3a-evidence.ps1",
    [string]$AutoPath = ".\phase3a-auto.ps1",
    [string]$ManifestPath = ".\phase3a-final-manifest.json",

    [string]$EvidenceZip = ".\phase3a_evidence_20260710_180530.zip",
    [string]$EvidenceDir = ".\phase3a_evidence_20260710_180530_extracted",

    [string]$ExpectedSha256 = "809F3C5CB6BEE651A9D051FEC626E7ECA20720851C085B77EC0749D6E6A492F5",

    [string]$CommitMessage = "fix(phase3a): harden evidence collection and finalize canonical artifact",

    [switch]$Push,
    [string]$Remote = "origin",
    [string]$Branch = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "=== $Message ===" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Resolve-RepoPath {
    param([string]$Path)
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return (Resolve-Path -LiteralPath $Path).Path
    }

    return (Resolve-Path -LiteralPath (Join-Path $RepoRoot $Path)).Path
}

function Assert-File {
    param([string]$Path, [string]$Name)

    $resolved = Resolve-RepoPath $Path
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        throw "$Name not found: $resolved"
    }

    return $resolved
}

function Assert-Directory {
    param([string]$Path, [string]$Name)

    $resolved = Resolve-RepoPath $Path
    if (-not (Test-Path -LiteralPath $resolved -PathType Container)) {
        throw "$Name not found: $resolved"
    }

    return $resolved
}

function Test-PowerShellSyntax {
    param([string]$Path)

    $tokens = $null
    $parseErrors = $null

    [System.Management.Automation.Language.Parser]::ParseFile(
        $Path,
        [ref]$tokens,
        [ref]$parseErrors
    ) | Out-Null

    if ($parseErrors.Count -gt 0) {
        $parseErrors | Format-List Message,ErrorId,Extent
        throw "Parser validation failed: $Path"
    }
}

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git command failed: git $($Args -join ' ')"
    }
}

Write-Step "Entering repository"
Set-Location -LiteralPath $RepoRoot
Write-Ok "Repo root: $RepoRoot"

Write-Step "Checking git repository"
Invoke-Git @("rev-parse", "--is-inside-work-tree") | Out-Null
Write-Ok "Git repository detected"

if ([string]::IsNullOrWhiteSpace($Branch)) {
    $Branch = (& git branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Branch)) {
        throw "Could not detect current git branch. Pass -Branch explicitly."
    }
}
Write-Ok "Branch: $Branch"

Write-Step "Resolving required artifacts"
$canonical = Assert-File $CanonicalPath "Canonical artifact"
$repair = Assert-File $RepairPath "Repair source"
$target = Assert-File $TargetPath "Compared target"
$collector = Assert-File $CollectorPath "Evidence collector"
$auto = Assert-File $AutoPath "Automation script"
$zip = Assert-File $EvidenceZip "Evidence zip"
$evidenceDirectory = Assert-Directory $EvidenceDir "Extracted evidence directory"

Write-Ok "Canonical: $canonical"
Write-Ok "Repair: $repair"
Write-Ok "Target: $target"
Write-Ok "Collector: $collector"
Write-Ok "Automation: $auto"
Write-Ok "Evidence zip: $zip"
Write-Ok "Evidence dir: $evidenceDirectory"

Write-Step "Parser validation"
Test-PowerShellSyntax $canonical
Test-PowerShellSyntax $repair
Test-PowerShellSyntax $target
Test-PowerShellSyntax $collector
Test-PowerShellSyntax $auto
Write-Ok "All PowerShell parser checks passed"

Write-Step "Hash validation"
$canonicalHash = (Get-FileHash -LiteralPath $canonical -Algorithm SHA256).Hash.ToUpperInvariant()
$repairHash = (Get-FileHash -LiteralPath $repair -Algorithm SHA256).Hash.ToUpperInvariant()

Write-Host "Canonical SHA256: $canonicalHash"
Write-Host "Repair SHA256   : $repairHash"

if ($canonicalHash -ne $ExpectedSha256.ToUpperInvariant()) {
    throw "Canonical hash mismatch. Expected $ExpectedSha256 but got $canonicalHash"
}

if ($repairHash -ne $ExpectedSha256.ToUpperInvariant()) {
    throw "Repair hash mismatch. Expected $ExpectedSha256 but got $repairHash"
}

if ($canonicalHash -ne $repairHash) {
    throw "Canonical and repair hashes do not match."
}

Write-Ok "Hash attestation passed"

Write-Step "Evidence validation"
$zipItem = Get-Item -LiteralPath $zip
if ($zipItem.Length -le 0) {
    throw "Evidence zip is empty: $zip"
}

$extractedFiles = Get-ChildItem -LiteralPath $evidenceDirectory -File -Recurse
if ($extractedFiles.Count -lt 1) {
    throw "Evidence directory contains no files: $evidenceDirectory"
}

Write-Ok "Evidence zip size: $($zipItem.Length) bytes"
Write-Ok "Extracted files: $($extractedFiles.Count)"

Write-Step "Writing final manifest"
$manifestFullPath = Join-Path $RepoRoot $ManifestPath

$manifest = [ordered]@{
    phase              = "3A"
    status             = "completed"
    completed_utc      = (Get-Date).ToUniversalTime().ToString("o")
    branch             = $Branch
    canonical_file     = $canonical
    canonical_sha256   = $canonicalHash
    repair_source      = $repair
    repair_sha256      = $repairHash
    target_compared    = $target
    collector_script   = $collector
    automation_script  = $auto
    evidence_zip       = $zip
    evidence_zip_size  = $zipItem.Length
    evidence_directory = $evidenceDirectory
    extracted_files    = $extractedFiles.Count
}

$manifest |
    ConvertTo-Json -Depth 10 |
    Set-Content -LiteralPath $manifestFullPath -Encoding UTF8

Write-Ok "Manifest written: $manifestFullPath"

Write-Step "Git status before staging"
Invoke-Git @("status", "--short")

Write-Step "Staging Phase 3A files"
$pathsToAdd = @(
    $CanonicalPath,
    $RepairPath,
    $TargetPath,
    $CollectorPath,
    $AutoPath,
    $ManifestPath,
    $EvidenceZip,
    $EvidenceDir
)

foreach ($path in $pathsToAdd) {
    if (Test-Path -LiteralPath (Join-Path $RepoRoot $path)) {
        Invoke-Git @("add", "--", $path)
        Write-Ok "Staged: $path"
    } else {
        Write-Warn "Skipped missing path: $path"
    }
}

Write-Step "Git staged diff summary"
Invoke-Git @("diff", "--cached", "--stat")

$stagedNames = (& git diff --cached --name-only)
if ($LASTEXITCODE -ne 0) {
    throw "Could not inspect staged files."
}

if (-not $stagedNames) {
    Write-Warn "No staged changes detected. Nothing to commit."
    exit 0
}

Write-Step "Creating commit"
$fullCommitMessage = @"
$CommitMessage

- fix evidence archive creation by using wildcard-aware Compress-Archive path handling
- enforce post-archive existence and non-empty validation
- add robust Phase 3A automation for parser validation, hashing, evidence detection, extraction, and promotion
- promote repair-phase3a-complete.ps1 to canonical asox-autopilot-phase3a.ps1
- add final manifest recording evidence, canonical artifact, and SHA256 attestation

Canonical SHA256:
$canonicalHash
"@

$tmpCommitMessage = Join-Path $env:TEMP ("phase3a-commit-message-" + [guid]::NewGuid().ToString("N") + ".txt")
Set-Content -LiteralPath $tmpCommitMessage -Value $fullCommitMessage -Encoding UTF8

try {
    Invoke-Git @("commit", "-F", $tmpCommitMessage)
}
finally {
    if (Test-Path -LiteralPath $tmpCommitMessage) {
        Remove-Item -LiteralPath $tmpCommitMessage -Force
    }
}

Write-Ok "Commit created"

Write-Step "Git status after commit"
Invoke-Git @("status", "--short")

if ($Push) {
    Write-Step "Pushing to GitHub"
    Invoke-Git @("push", $Remote, $Branch)
    Write-Ok "Pushed to $Remote/$Branch"
} else {
    Write-Warn "Push skipped. Run again with -Push to upload to GitHub."
    Write-Host "Example:"
    Write-Host "  .\save-phase3a-github.ps1 -Push"
}

Write-Step "Completed"
Write-Ok "Phase 3A is committed locally."
if ($Push) {
    Write-Ok "Phase 3A is pushed to GitHub."
}
