[CmdletBinding()]
param(
  [string]$BaseBranch = "main",
  [switch]$DoPush,
  [switch]$DoCreateOrUpdatePr
)

$ErrorActionPreference = "Stop"

function Step([string]$Message) {
  Write-Host ""
  Write-Host "==> $Message" -ForegroundColor Cyan
}

function Get-GitStatusLines {
  $lines = @(git status --porcelain)
  if ($LASTEXITCODE -ne 0) {
    throw "git status failed."
  }
  return $lines
}

function Require-CleanWorktree([string]$ContextMessage = "Working tree is not clean.") {
  $statusLines = Get-GitStatusLines
  if ($statusLines.Count -gt 0) {
    Write-Host ""
    Write-Host "Git status:" -ForegroundColor Yellow
    $statusLines | ForEach-Object { Write-Host $_ }
    throw "$ContextMessage Commit, stash, or discard changes first."
  }
}

function Require-Command([string]$Name) {
  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  return $null -ne $cmd
}

function Test-OnlyEvidenceTimestampDiff([string]$RelativePath) {
  $diffLines = @(git diff --unified=0 -- $RelativePath)
  if ($LASTEXITCODE -ne 0) {
    throw "git diff failed for $RelativePath"
  }

  if ($diffLines.Count -eq 0) {
    return $false
  }

  $meaningful = @()

  foreach ($line in $diffLines) {
    if (
      $line.StartsWith("diff --git ") -or
      $line.StartsWith("index ") -or
      $line.StartsWith("--- ") -or
      $line.StartsWith("+++ ") -or
      $line.StartsWith("@@ ")
    ) {
      continue
    }

    if ($line.StartsWith("-") -or $line.StartsWith("+")) {
      $meaningful += $line
    }
  }

  if ($meaningful.Count -ne 2) {
    return $false
  }

  $removed = $meaningful[0]
  $added = $meaningful[1]

  if (-not $removed.StartsWith("-")) {
    return $false
  }

  if (-not $added.StartsWith("+")) {
    return $false
  }

  $removedBody = $removed.Substring(1).Trim()
  $addedBody = $added.Substring(1).Trim()

  if ($removedBody -notmatch '^"generated_at_utc"\s*:\s*"[^"]+",?$') {
    return $false
  }

  if ($addedBody -notmatch '^"generated_at_utc"\s*:\s*"[^"]+",?$') {
    return $false
  }

  return $true
}

function Resolve-AllowedPostVerifyChanges {
  $statusLines = Get-GitStatusLines
  if ($statusLines.Count -eq 0) {
    return
  }

  $allowedEvidencePath = "artifacts/mcp03-evidence.json"
  $statusBody = @($statusLines | ForEach-Object { $_.Trim() })

  if ($statusBody.Count -eq 1) {
    $entry = $statusBody[0]
    if ($entry.EndsWith($allowedEvidencePath) -and (Test-OnlyEvidenceTimestampDiff $allowedEvidencePath)) {
      Write-Host ""
      Write-Host "Only evidence timestamp changed; restoring artifact to keep PR flow deterministic." -ForegroundColor Yellow
      git restore -- $allowedEvidencePath
      if ($LASTEXITCODE -ne 0) {
        throw "git restore failed for $allowedEvidencePath"
      }
      return
    }
  }

  Write-Host ""
  Write-Host "Verification changed tracked files:" -ForegroundColor Yellow
  $statusLines | ForEach-Object { Write-Host $_ }
  Write-Host ""
  Write-Host "Most likely refreshed artifacts need review and commit." -ForegroundColor Yellow
  Write-Host "Suggested next commands:" -ForegroundColor Yellow
  Write-Host "  git add artifacts out/pr"
  Write-Host '  git commit -m "refresh MCP-03 evidence artifacts"'
  Write-Host "  git push"
  throw "Verification produced uncommitted changes. PR flow stopped to avoid publishing stale evidence."
}

if ($PSCommandPath) {
  $scriptRoot = Split-Path -Parent $PSCommandPath
} else {
  $scriptRoot = (Get-Location).Path
}

Set-Location $scriptRoot

$branch = git rev-parse --abbrev-ref HEAD
if ($LASTEXITCODE -ne 0) {
  throw "Unable to determine current git branch."
}

$commitBeforeVerify = git rev-parse --short HEAD
if ($LASTEXITCODE -ne 0) {
  throw "Unable to determine current commit."
}

$prTitle = "MCP-03 bootstrap verification and evidence refresh"
$outDir = Join-Path $scriptRoot "out\pr"
$prBodyPath = Join-Path $outDir "mcp03-pr-body.md"
$bootstrapScript = Join-Path $scriptRoot "scripts\build-mcp03-evidence.ps1"

Step "Checking working tree before verification"
Require-CleanWorktree "Working tree is not clean before verification."

Step "Locating bootstrap script"
if (-not (Test-Path $bootstrapScript)) {
  throw "Bootstrap script not found: $bootstrapScript"
}

Step "Running bootstrap verification"
& powershell -ExecutionPolicy Bypass -File $bootstrapScript
if ($LASTEXITCODE -ne 0) {
  throw "build-mcp03-evidence.ps1 failed."
}

Step "Checking working tree after verification"
Resolve-AllowedPostVerifyChanges
Require-CleanWorktree "Working tree is not clean after verification."

Step "Building PR body"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$commitAfterVerify = git rev-parse --short HEAD
if ($LASTEXITCODE -ne 0) {
  throw "Unable to determine current commit after verification."
}

$lines = @(
  "## Summary",
  "",
  "- Refresh MCP-03 bootstrap and verification flow.",
  "- Re-run static analysis, unit, replay, property, and formal smoke checks.",
  "- Regenerate evidence artifacts for review.",
  "",
  "## Verification",
  "",
  "- bootstrap script: ``scripts/build-mcp03-evidence.ps1``",
  "- branch: ``$branch``",
  "- commit: ``$commitAfterVerify``",
  "",
  "## Notes",
  "",
  "- PR body generated by ``pr-mcp03.ps1``.",
  "- Evidence artifacts should be available under ``artifacts/``."
)

Set-Content -Path $prBodyPath -Value $lines -Encoding UTF8

Step "Checking working tree after PR body generation"
$statusAfterPrBody = Get-GitStatusLines
if ($statusAfterPrBody.Count -gt 0) {
  Write-Host ""
  Write-Host "PR body generation changed tracked files:" -ForegroundColor Yellow
  $statusAfterPrBody | ForEach-Object { Write-Host $_ }
  throw "PR flow stopped because generating the PR body left uncommitted changes."
}

Write-Host ""
Write-Host "PR body written to: $prBodyPath" -ForegroundColor Green

if ($DoPush) {
  Step "Pushing branch"
  git push -u origin $branch
  if ($LASTEXITCODE -ne 0) {
    throw "git push failed."
  }
} else {
  Write-Host ""
  Write-Host "Skipping push. Re-run with -DoPush to publish the branch."
}

if ($DoCreateOrUpdatePr) {
  Step "Creating or updating PR"

  if (-not (Require-Command "gh")) {
    Write-Host ""
    Write-Host "GitHub CLI not found; PR body is ready." -ForegroundColor Yellow
    Write-Host "Create the PR manually with:"
    Write-Host "  base: $BaseBranch"
    Write-Host "  head: $branch"
    Write-Host "  title: $prTitle"
    Write-Host "  body file: $prBodyPath"
  } else {
    $existingPr = gh pr list --head $branch --base $BaseBranch --json number --jq ".[0].number"
    if ($LASTEXITCODE -ne 0) {
      throw "Unable to query existing PRs with gh."
    }

    if ($existingPr) {
      gh pr edit $existingPr --title $prTitle --body-file $prBodyPath
      if ($LASTEXITCODE -ne 0) {
        throw "gh pr edit failed."
      }
    } else {
      gh pr create --base $BaseBranch --head $branch --title $prTitle --body-file $prBodyPath
      if ($LASTEXITCODE -ne 0) {
        throw "gh pr create failed."
      }
    }
  }
} else {
  Write-Host ""
  Write-Host "Skipping PR creation. Re-run with -DoCreateOrUpdatePr to use gh."
}

Write-Host ""
Write-Host "Final branch status:"
git status --short

Write-Host ""
Write-Host "Done." -ForegroundColor Green
