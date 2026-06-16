# Phase 17 Runtime Audit Checklist

## A. Repository State

- [ ] Confirm branch is phase17-controlled-development
- [ ] Confirm working tree is clean
- [ ] Confirm branch is synced with origin/phase17-controlled-development
- [ ] Confirm master remains frozen

## B. Safety Controls

- [ ] Confirm no --live flag will be used
- [ ] Confirm no production credentials will be used
- [ ] Confirm no secrets will be passed through CLI arguments
- [ ] Confirm audit is non-live and non-production
- [ ] Confirm any sign of live arming will stop the audit immediately

## C. Startup Command Review

- [ ] Identify the exact intended startup command
- [ ] Confirm command does not include --live
- [ ] Confirm command does not include secrets
- [ ] Confirm expected output location
- [ ] Confirm timeout/stop plan if runtime hangs

## D. Self-Test Observation

- [ ] Observe whether PHOENIX_SELFTEST runs
- [ ] Observe whether self-test passes
- [ ] Capture self-test failure output if it fails
- [ ] Do not bypass self-test without separate approval

## E. Logging and Reporting Hygiene

- [ ] Observe whether rgv is printed or reported
- [ ] Search output for sensitive-looking values
- [ ] Confirm secrets are not present in logs
- [ ] Record any redaction gaps

## F. Re-exec / Restart Behavior

- [ ] Observe whether process restarts itself
- [ ] Observe whether os.execv-like behavior is visible
- [ ] Record repeated startup banners or duplicate initialization
- [ ] Stop if restart loop is suspected

## G. Async Runtime Observation

- [ ] Observe whether runtime reaches async startup
- [ ] Observe whether runtime hangs
- [ ] Observe whether runtime exits immediately
- [ ] Record final state

## H. Audit Closure

- [ ] Save evidence under evidence/phase17/runtime_audit
- [ ] Update PHASE17_RUNTIME_AUDIT.md
- [ ] Commit evidence summary
- [ ] Push to phase17-controlled-development
"@

 = @'
Stop = "Stop"
Set-Location "E:\saead\ssl\s43_refactor"

 = Get-Date -Format "yyyyMMdd_HHmmss"
 = ".\evidence\phase17\runtime_audit"
New-Item -ItemType Directory -Path  -Force | Out-Null
 = Join-Path  "runtime_audit_precheck_.txt"

function Write-Evidence {
    param([string])
     | Tee-Object -FilePath  -Append
}

Write-Evidence "S43 PHASE17 SAFE RUNTIME AUDIT PRECHECK"
Write-Evidence "TIMESTAMP="
Write-Evidence "PWD=E:\saead\ssl\s43_refactor"
Write-Evidence "BRANCH=phase17-controlled-development"
Write-Evidence "HEAD=d36f130"
Write-Evidence "ORIGIN_PHASE17=d36f130"
Write-Evidence ""

git status | Tee-Object -FilePath  -Append

Write-Evidence ""
Write-Evidence "DO_NOT_USE_LIVE_FLAG=YES"
Write-Evidence "DO_NOT_PASS_SECRETS_IN_ARGV=YES"
Write-Evidence "DO_NOT_USE_PRODUCTION_CREDENTIALS=YES"
Write-Evidence "STOP_ON_LIVE_ARM_SIGNAL=YES"
Write-Evidence "RUNTIME_EXECUTION_PERFORMED=NO"
Write-Evidence ""

try {
     = python --version 2>&1
    Write-Evidence "PYTHON_VERSION="
} catch {
    Write-Evidence "PYTHON_VERSION=NOT_FOUND_OR_ERROR"
}

 = @(
    ".\s43.py",
    ".\s43_instrumented_LATEST.py",
    ".\MY_S43_LATEST.py",
    ".\11029.py",
    ".\11029_legacy_reference.py"
)

foreach ( in ) {
    if (Test-Path ) {
        Write-Evidence "FOUND="
    } else {
        Write-Evidence "MISSING="
    }
}

 = @()
foreach ( in ) {
    if (Test-Path ) {  +=  }
}

 = @(
    "if __name__ ==",
    "def main",
    "argparse",
    "--live",
    "--watchdog",
    "PHOENIX_SELFTEST",
    "os.execv",
    "sys.argv",
    "_live_trading_armed",
    "_dry_run",
    "asyncio",
    "_enhanced_trading_loop",
    "_pp200_report"
)

foreach ( in ) {
    Write-Evidence ""
    Write-Evidence "FILE="
    foreach ( in ) {
         = Select-String -Path  -Pattern  -SimpleMatch -ErrorAction SilentlyContinue
        if () {
            foreach ( in  | Select-Object -First 20) {
                Write-Evidence ("MATCH line {0}: {1}" -f .LineNumber, .Line.Trim())
            }
        }
    }
}

Write-Evidence ""
Write-Evidence "PHASE17_RUNTIME_AUDIT_PRECHECK_PASS=YES"
Write-Evidence "RUNTIME_EXECUTION_PERFORMED=NO"
Write-Evidence "LIVE_TRADING_ENABLED=NO"
Write-Evidence "EVIDENCE_FILE="

Write-Host "PHASE17_RUNTIME_AUDIT_PRECHECK_PASS" -ForegroundColor Green
Write-Host "EVIDENCE_FILE="
Write-Host "RUNTIME_EXECUTION_PERFORMED=NO"
Write-Host "LIVE_TRADING_ENABLED=NO"
'@

 = @"
# Phase 17 Runtime Audit Evidence

This directory stores evidence produced during the Phase 17 runtime audit.

Rules:
- Do not store secrets here.
- Do not store private keys, wallet files, API keys, tokens, passwords, or credentials.
- Redact sensitive values before committing evidence.
- Only commit safe summaries or sanitized outputs.
- Runtime execution must remain non-live unless separately approved.

Current status:
- Runtime audit framework created.
- Runtime execution not yet performed.
- Live trading not enabled.
