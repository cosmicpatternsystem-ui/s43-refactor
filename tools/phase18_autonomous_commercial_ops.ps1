param(
    [string]$Message = "",
    [string]$AuditPrefix = "PHASE18_AUTONOMOUS_COMMERCIAL_OPS"
)

$ErrorActionPreference = "Stop"

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$root = Resolve-Path "."
$auditDir = Join-Path ".\AUDIT" "$AuditPrefix`_$ts"
New-Item -ItemType Directory -Force -Path $auditDir | Out-Null

function Write-Capture {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][scriptblock]$Command
    )
    $outFile = Join-Path $auditDir $Name
    try {
        & $Command *>&1 | Out-File -Encoding utf8 $outFile
        "EXIT_CODE=$LASTEXITCODE" | Out-File -Encoding utf8 -Append $outFile
    } catch {
        $_ | Out-File -Encoding utf8 $outFile
        "EXIT_CODE=1" | Out-File -Encoding utf8 -Append $outFile
        throw
    }
}

function Test-EnvPresence {
    param([string]$Name)
    $value = [Environment]::GetEnvironmentVariable($Name)
    if ([string]::IsNullOrWhiteSpace($value)) {
        return "MISSING"
    }
    return "PRESENT"
}

Write-Capture "01_branch.txt" { git rev-parse --abbrev-ref HEAD }
Write-Capture "02_head.txt" { git rev-parse HEAD }
Write-Capture "03_origin_head.txt" { git rev-parse origin/phase17-work-from-restore }
Write-Capture "04_status_short.txt" { git status --short }
Write-Capture "05_latest_commit.txt" { git log -1 --pretty=fuller }
Write-Capture "06_remote.txt" { git remote -v }
Write-Capture "07_preflight_audit.txt" { & cmd.exe /d /c "powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\phase18_preflight_audit.ps1 2>&1" }
Write-Capture "08_security_audit.txt" { & cmd.exe /d /c "powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\phase18_readonly_security_audit.ps1 2>&1" }
Write-Capture "09_stability_audit.txt" { & cmd.exe /d /c "powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\phase18_stability_test_readiness_audit.ps1 2>&1" }

$openaiStatus = Test-EnvPresence "OPENAI_API_KEY"
$anthropicStatus = Test-EnvPresence "ANTHROPIC_API_KEY"
$githubTokenStatus = Test-EnvPresence "GITHUB_TOKEN"

$head = git rev-parse HEAD
$origin = git rev-parse origin/phase17-work-from-restore
$branch = git rev-parse --abbrev-ref HEAD
$subject = git log -1 --pretty=%s
$statusShort = git status --short
$preflightText = Get-Content (Join-Path $auditDir "07_preflight_audit.txt") -Raw

$result = "REVIEW_REQUIRED"
if (($head -eq $origin) -and ([string]::IsNullOrWhiteSpace($statusShort)) -and ($preflightText -match "PHASE18_PREFLIGHT_AUDIT_PASS") -and ($preflightText -match "WORKING_TREE=CLEAN")) {
    $result = "PASS"
}

@"
PHASE18 AUTONOMOUS COMMERCIAL OPS REPORT
TIMESTAMP=$ts
ROOT=$root
BRANCH=$branch
HEAD=$head
ORIGIN=$origin
LATEST_SUBJECT=$subject
RESULT=$result
OPENAI_API_KEY=$openaiStatus
ANTHROPIC_API_KEY=$anthropicStatus
GITHUB_TOKEN=$githubTokenStatus
SECRET_VALUES_DISCLOSED=NO
PREFLIGHT_CAPTURED=YES
SECURITY_AUDIT_CAPTURED=YES
STABILITY_AUDIT_CAPTURED=YES
"@ | Out-File -Encoding utf8 (Join-Path $auditDir "00_autonomous_commercial_ops_report.txt")

if ([string]::IsNullOrWhiteSpace($Message)) {
    $Message = "audit: add phase18 autonomous commercial ops evidence $ts"
}

& .\tools\phase18_approved_sync_wrapper.ps1 -Message $Message -Paths @($auditDir)

git status --short
git rev-parse HEAD
git rev-parse origin/phase17-work-from-restore
& .\tools\phase18_preflight_audit.ps1
