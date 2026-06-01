#!/usr/bin/env bash
set -u

echo "== Phase 9 Checkpoint Verification =="
echo "Mode: read-only verification"
echo

FAIL=0
WARN=0

require_file() {
  local file="$1"
  if [ -f "$file" ]; then
    echo "PASS: required file exists: $file"
  else
    echo "FAIL: required file missing: $file"
    FAIL=$((FAIL + 1))
  fi
}

require_grep() {
  local pattern="$1"
  local file="$2"
  local label="$3"

  if [ ! -f "$file" ]; then
    echo "FAIL: cannot check missing file: $file"
    FAIL=$((FAIL + 1))
    return
  fi

  if grep -qi -- "$pattern" "$file"; then
    echo "PASS: $label found in $file"
  else
    echo "FAIL: $label not found in $file"
    FAIL=$((FAIL + 1))
  fi
}

warn_grep() {
  local pattern="$1"
  local file="$2"
  local label="$3"

  if [ ! -f "$file" ]; then
    echo "WARN: cannot warning-check missing file: $file"
    WARN=$((WARN + 1))
    return
  fi

  if grep -qi -- "$pattern" "$file"; then
    echo "PASS: $label found in $file"
  else
    echo "WARN: $label not found in $file"
    WARN=$((WARN + 1))
  fi
}

reject_grep() {
  local pattern="$1"
  local file="$2"
  local label="$3"

  if [ ! -f "$file" ]; then
    echo "WARN: cannot reject-check missing file: $file"
    WARN=$((WARN + 1))
    return
  fi

  if grep -qi -- "$pattern" "$file"; then
    echo "FAIL: prohibited wording found in $file: $label"
    FAIL=$((FAIL + 1))
  else
    echo "PASS: prohibited wording absent from $file: $label"
  fi
}

echo "-- Git status --"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if [ -z "$(git status --short)" ]; then
    echo "PASS: working tree is clean"
  else
    echo "FAIL: working tree is not clean"
    git status --short
    FAIL=$((FAIL + 1))
  fi
else
  echo "FAIL: not inside a git repository"
  FAIL=$((FAIL + 1))
fi

echo
echo "-- Required Phase 9 files --"
require_file "docs/roadmap/PHASE9_VALIDATION_PLAN.md"
require_file "docs/roadmap/PHASE9_VALIDATION_CHECKLIST.md"
require_file "docs/roadmap/PHASE9_EVIDENCE_TEMPLATE.md"
require_file "docs/roadmap/PHASE9_CHECKPOINT_STATUS.md"
require_file "docs/roadmap/PHASE9_REVIEW_INTAKE.md"

echo
echo "-- Supporting context files --"
require_file "docs/roadmap/PHASE8_HANDOFF_NOTE.md"
require_file "docs/roadmap/TOP_LEVEL_READINESS_GATE.md"

echo
echo "-- Safety posture checks --"
for file in \
  docs/roadmap/PHASE9_VALIDATION_PLAN.md \
  docs/roadmap/PHASE9_VALIDATION_CHECKLIST.md \
  docs/roadmap/PHASE9_EVIDENCE_TEMPLATE.md \
  docs/roadmap/PHASE9_CHECKPOINT_STATUS.md \
  docs/roadmap/PHASE9_REVIEW_INTAKE.md
do
  require_grep "SAFE-NO-TRADE" "$file" "SAFE-NO-TRADE safety posture"
done

echo
echo "-- Non-authorization / blocked-action checks --"
require_grep "runtime activation" "docs/roadmap/PHASE9_CHECKPOINT_STATUS.md" "runtime activation boundary"
require_grep "recovery activation" "docs/roadmap/PHASE9_CHECKPOINT_STATUS.md" "recovery activation boundary"
require_grep "live trading" "docs/roadmap/PHASE9_CHECKPOINT_STATUS.md" "live trading boundary"
require_grep "production-readiness" "docs/roadmap/PHASE9_CHECKPOINT_STATUS.md" "production-readiness boundary"
require_grep "Blocked Actions" "docs/roadmap/PHASE9_CHECKPOINT_STATUS.md" "blocked actions section"

require_grep "review" "docs/roadmap/PHASE9_REVIEW_INTAKE.md" "review wording"
require_grep "SAFE-NO-TRADE" "docs/roadmap/PHASE9_REVIEW_INTAKE.md" "SAFE-NO-TRADE boundary"
warn_grep "non-author" "docs/roadmap/PHASE9_REVIEW_INTAKE.md" "non-authorization wording"
warn_grep "does not authorize" "docs/roadmap/PHASE9_REVIEW_INTAKE.md" "explicit non-authorization wording"

warn_grep "non-goals" "docs/roadmap/PHASE9_VALIDATION_PLAN.md" "non-goals wording"
warn_grep "blocked" "docs/roadmap/PHASE9_VALIDATION_CHECKLIST.md" "blocked wording"
warn_grep "evidence" "docs/roadmap/PHASE9_EVIDENCE_TEMPLATE.md" "evidence wording"
warn_grep "review" "docs/roadmap/PHASE9_CHECKPOINT_STATUS.md" "review wording"

echo
echo "-- False readiness claim checks --"
for file in \
  docs/roadmap/PHASE9_VALIDATION_PLAN.md \
  docs/roadmap/PHASE9_VALIDATION_CHECKLIST.md \
  docs/roadmap/PHASE9_EVIDENCE_TEMPLATE.md \
  docs/roadmap/PHASE9_CHECKPOINT_STATUS.md \
  docs/roadmap/PHASE9_REVIEW_INTAKE.md
do
  reject_grep "production ready" "$file" "unqualified production ready claim"
  reject_grep "live trading approved" "$file" "live trading approval claim"
  reject_grep "runtime ready" "$file" "unqualified runtime ready claim"
  reject_grep "runtime activation approved" "$file" "runtime activation approval claim"
  reject_grep "recovery activation approved" "$file" "recovery activation approval claim"
done

echo
echo "-- Script syntax sanity --"
SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
if command -v bash >/dev/null 2>&1; then
  if [ -f "$SCRIPT_PATH" ]; then
    if bash -n "$SCRIPT_PATH"; then
      echo "PASS: verifier script syntax is valid"
    else
      echo "FAIL: verifier script syntax is invalid"
      FAIL=$((FAIL + 1))
    fi
  else
    echo "WARN: verifier script path is not a regular file: $SCRIPT_PATH"
    WARN=$((WARN + 1))
  fi
else
  echo "WARN: bash command not found for syntax check"
  WARN=$((WARN + 1))
fi

echo
echo "== Summary =="
echo "Failures: $FAIL"
echo "Warnings: $WARN"

if [ "$FAIL" -eq 0 ]; then
  if [ "$WARN" -eq 0 ]; then
    echo "RESULT: PASS"
  else
    echo "RESULT: PASS WITH WARNINGS"
  fi
  echo "Phase 9 checkpoint is verification-ready under SAFE-NO-TRADE."
  exit 0
else
  echo "RESULT: FAIL"
  echo "Phase 9 checkpoint requires review before freeze."
  exit 1
fi
