param([switch]$NoGit,[switch]$SkipAssert)
$ErrorActionPreference = "Stop"
$repoRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0 -or -not $repoRoot) { $repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..") }
$repoRoot = "$repoRoot".Trim()
Set-Location $repoRoot
New-Item -ItemType Directory -Force -Path "AUDIT" | Out-Null
$now = Get-Date -Format "yyyy-MM-dd HH:mm:ss K"
if ($NoGit) { $branch = "UNKNOWN"; $commit = "UNKNOWN"; $fullCommit = "UNKNOWN"; $statusRaw = ""; $recentCommits = "UNKNOWN" }
else { $branch = git rev-parse --abbrev-ref HEAD; $commit = git rev-parse --short HEAD; $fullCommit = git rev-parse HEAD; $statusRaw = git status --porcelain; $recentCommits = (git log --oneline -5) -join "`n" }
$repoState = if ([string]::IsNullOrWhiteSpace($statusRaw)) { "CLEAN" } else { "DIRTY" }
$decision = @("# Phase18 Release Readiness Decision","","Generated: $now","","## Binding Decision","","Refactor is frozen. The project is now in stabilization mode.","","## Mandatory State","","- Project Mode: STABILIZATION_MODE","- Refactor Status: FROZEN","- Commercial Readiness: PARTIAL -> RELEASE_CANDIDATE_TARGET","- Automation Readiness: STRONG","- Audit Readiness: ACTIVE","- Next Gate: GO / NO-GO RELEASE DECISION","","Canonical source of truth: AUDIT/RELEASE_READINESS_MASTER.md")
$snapshot = @("# Phase18 Release Readiness Snapshot","","Generated: $now","","## Repository Snapshot","","- Branch: $branch","- Commit: $commit","- Full Commit: $fullCommit","- Working Tree: $repoState","","## Recent Commits","","
````text",$recentCommits,"
````","","Canonical source of truth: AUDIT/RELEASE_READINESS_MASTER.md")
$master = @("# S43 Release Readiness Master","","Generated: $now","","## Canonical Rule","","This document is the single source of truth for release-readiness status.","Supporting AUDIT files are evidence only.","Do not create parallel roadmap, readiness, or decision documents.","","## Operational Contract","","This is enforced by AUDIT/RELEASE_READINESS_POLICY.json and tools/assert_release_readiness.ps1.","","## Current Status","","- Project Mode: STABILIZATION_MODE","- Refactor Status: FROZEN","- Commercial Readiness: PARTIAL -> RELEASE_CANDIDATE_TARGET","- Automation Readiness: STRONG","- Audit Readiness: ACTIVE","- Next Gate: GO / NO-GO RELEASE DECISION","","## Current Business Decision","","Refactor work is frozen. The project has moved into stabilization, release-readiness validation, release packaging, and final GO / NO-GO decision management.","","Commercial launch is not declared final until the GO / NO-GO gate passes.","","## Repository State","","- Branch: $branch","- Commit: $commit","- Full Commit: $fullCommit","- Working Tree: $repoState","","## Recent Commits","","
````text",$recentCommits,"
````","","## Mandatory Behavior","","- Release readiness must be generated through tooling.","- Canonical status must remain in AUDIT/RELEASE_READINESS_MASTER.md.","- Supporting files are evidence only.","- Final release requires GO / NO-GO approval.","- Dirty working tree is not acceptable for final readiness assertion.","","## Known Gaps Before Final Release","","- CI evidence required.","- Security scan required.","- Release packaging required.","- Final GO / NO-GO decision pending.")
Set-Content -Path "AUDIT/PHASE18_RELEASE_READINESS_DECISION.md" -Value $decision -Encoding UTF8
Set-Content -Path "AUDIT/PHASE18_RELEASE_READINESS_SNAPSHOT.md" -Value $snapshot -Encoding UTF8
Set-Content -Path "AUDIT/RELEASE_READINESS_MASTER.md" -Value $master -Encoding UTF8
Write-Host "Release readiness files generated."
if (-not $SkipAssert) { powershell -NoProfile -ExecutionPolicy Bypass -File "tools/assert_release_readiness.ps1" -AllowDirty }
