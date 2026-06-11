#!/usr/bin/env sh
set -eu

echo "=== Top-Level Readiness Check ==="
echo

failures=0
warnings=0

fail() {
  echo "FAIL: $1"
  failures=$((failures + 1))
}

warn() {
  echo "WARN: $1"
  warnings=$((warnings + 1))
}

ok() {
  echo "OK: $1"
}

tmp_dir="${TMPDIR:-}"
if [ -z "$tmp_dir" ]; then
  if [ -d /tmp ]; then
    tmp_dir="/tmp"
  else
    tmp_dir=".tmp"
  fi
fi

mkdir -p "$tmp_dir"

safe_scan_file="$tmp_dir/top_level_safe_scan.txt"
report="$tmp_dir/top_level_readiness_report.txt"

echo "[1/7] Git repo"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  ok "Inside git repository"
else
  fail "Not inside git repository"
fi
echo

echo "[2/7] Working tree"
if [ -n "$(git status --short)" ]; then
  fail "Working tree is not clean"
  git status --short
else
  ok "Working tree is clean"
fi
echo

echo "[3/7] Required documents"
for f in \
  docs/roadmap/PHASE8_PROGRESS.md \
  docs/roadmap/PHASE8_RECOVERY_ACCEPTANCE.md \
  docs/roadmap/PHASE8_RECOVERY_TOUCHPOINTS.md \
  docs/roadmap/TOP_LEVEL_READINESS_GATE.md
do
  if [ -f "$f" ]; then
    ok "$f exists"
  else
    warn "$f missing"
  fi
done
echo

echo "[4/7] Syntax"
if [ -f s43.py ]; then
  if python3 -m py_compile s43.py; then
    ok "s43.py syntax OK"
  else
    fail "s43.py syntax failed"
  fi
else
  warn "s43.py not found"
fi

if [ -f run_hardening_tests.py ]; then
  if python3 -m py_compile run_hardening_tests.py; then
    ok "run_hardening_tests.py syntax OK"
  else
    fail "run_hardening_tests.py syntax failed"
  fi
else
  warn "run_hardening_tests.py not found"
fi
echo

echo "[5/7] Hardening tests"
if [ -f run_hardening_tests.py ]; then
  if python3 run_hardening_tests.py; then
    ok "hardening tests passed"
  else
    fail "hardening tests failed"
  fi
else
  warn "hardening test runner missing; skipped"
fi
echo

echo "[6/7] Safety scan"
scan_targets=""
[ -f s43.py ] && scan_targets="$scan_targets s43.py"
[ -d docs ] && scan_targets="$scan_targets docs"

if [ -n "$scan_targets" ]; then
  if grep -RIn "SAFE-NO-TRADE" $scan_targets > "$safe_scan_file" 2>/dev/null; then
    ok "SAFE-NO-TRADE reference found"
  else
    warn "SAFE-NO-TRADE reference not found"
  fi
else
  warn "No scan targets found"
fi
echo

echo "[7/7] Report"
{
  echo "Top-Level Readiness Report"
  echo "Generated at: $(date)"
  echo
  echo "Branch:"
  git branch --show-current || true
  echo
  echo "Recent commits:"
  git log --oneline -5 || true
  echo
  echo "Working tree:"
  git status --short || true
  echo
  echo "Failures: $failures"
  echo "Warnings: $warnings"
  echo
  if [ "$failures" -eq 0 ]; then
    echo "Result: no blocking failures detected by checker"
  else
    echo "Result: blocked"
  fi
  echo
  echo "Safety recommendation: keep SAFE-NO-TRADE"
  echo "Report path: $report"
  echo "Safety scan path: $safe_scan_file"
} > "$report"

ok "Report written to $report"
cat "$report"
echo

if [ "$failures" -ne 0 ]; then
  echo "=== RESULT: BLOCKED ==="
  exit 1
fi

echo "=== RESULT: PASS WITH REVIEW REQUIREMENTS ==="
