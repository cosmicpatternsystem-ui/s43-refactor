#!/usr/bin/env bash
set -u

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$PROJECT_DIR/s43.py"
TOOLKIT="$PROJECT_DIR/s43_toolkit.sh"

CANDIDATES="$PROJECT_DIR/candidates"
PATCHES="$PROJECT_DIR/patches"
BACKUPS="$PROJECT_DIR/backups"
LOGS="$PROJECT_DIR/logs"
SUMMARIES="$PROJECT_DIR/summaries"
REPORTS="$PROJECT_DIR/reports"

mkdir -p "$CANDIDATES" "$PATCHES" "$BACKUPS" "$LOGS" "$SUMMARIES" "$REPORTS"

ts() {
  date +"%Y%m%d_%H%M%S"
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

need_target() {
  [ -f "$TARGET" ] || die "s43.py not found: $TARGET"
}

need_toolkit() {
  [ -x "$TOOLKIT" ] || die "s43_toolkit.sh not executable or not found: $TOOLKIT"
}

cmd_status() {
  echo "S43_SELFPATCH_STATUS"
  echo "PROJECT_DIR=$PROJECT_DIR"
  echo "TARGET=$TARGET"
  echo "TOOLKIT=$TOOLKIT"
  echo "CANDIDATES=$CANDIDATES"
  echo "PATCHES=$PATCHES"
  echo "BACKUPS=$BACKUPS"
  echo "LOGS=$LOGS"
  echo "SUMMARIES=$SUMMARIES"
  echo "REPORTS=$REPORTS"
  echo
  echo "Latest candidate:"
  ls -1t "$CANDIDATES"/s43_candidate_*.py 2>/dev/null | head -1 || true
  echo
  echo "Latest backup:"
  ls -1t "$BACKUPS"/s43_before_promote_*.py 2>/dev/null | head -1 || true
}

cmd_new_candidate() {
  need_target
  T="$(ts)"
  OUT="$CANDIDATES/s43_candidate_${T}.py"
  cp -p "$TARGET" "$OUT" || die "copy candidate failed"
  python -m py_compile "$OUT" || die "candidate compile failed"
  echo "CANDIDATE_CREATED=$OUT"
  echo "COMPILE_OK"
  echo
  echo "Edit this safely:"
  echo "nano \"$OUT\""
  echo
  echo "Then check:"
  echo "./s43_selfpatch.sh check \"$OUT\""
}

cmd_check() {
  C="${1:-}"
  [ -n "$C" ] || die "usage: ./s43_selfpatch.sh check candidates/s43_candidate_x.py"
  [ -f "$C" ] || die "candidate not found: $C"

  echo "CHECK_CANDIDATE=$C"
  python -m py_compile "$C" || die "COMPILE_FAIL"

  echo "COMPILE_OK"

  if [ -f "$TARGET" ]; then
    D="$PATCHES/diff_$(ts).patch"
    diff -u "$TARGET" "$C" > "$D" || true
    echo "DIFF_SAVED=$D"
    echo "---- DIFF HEAD ----"
    sed -n '1,120p' "$D"
    echo "---- DIFF END ----"
  fi
}

cmd_promote() {
  need_target
  need_toolkit

  C="${1:-}"
  [ -n "$C" ] || die "usage: ./s43_selfpatch.sh promote candidates/s43_candidate_x.py"
  [ -f "$C" ] || die "candidate not found: $C"

  T="$(ts)"
  B="$BACKUPS/s43_before_promote_${T}.py"
  D="$PATCHES/promote_diff_${T}.patch"
  R="$REPORTS/promote_report_${T}.txt"

  echo "PROMOTE_START timestamp=$T" | tee "$R"
  echo "TARGET=$TARGET" | tee -a "$R"
  echo "CANDIDATE=$C" | tee -a "$R"
  echo "BACKUP=$B" | tee -a "$R"

  python -m py_compile "$C" || die "candidate compile failed; production unchanged"

  cp -p "$TARGET" "$B" || die "backup failed; production unchanged"
  diff -u "$TARGET" "$C" > "$D" || true
  echo "DIFF=$D" | tee -a "$R"

  cp -p "$C" "$TARGET" || {
    cp -p "$B" "$TARGET" 2>/dev/null || true
    die "promote copy failed; rollback attempted"
  }

  python -m py_compile "$TARGET" || {
    echo "POST_PROMOTE_COMPILE_FAIL -> rollback" | tee -a "$R"
    cp -p "$B" "$TARGET"
    die "rollback done after compile fail"
  }

  echo "POST_PROMOTE_COMPILE_OK" | tee -a "$R"

  echo "RUN_TOOLKIT_VERIFY" | tee -a "$R"
  "$TOOLKIT" verify | tee -a "$R"
  RC="${PIPESTATUS[0]}"

  if grep -q "RESULT: PASS" "$R"; then
    echo "PROMOTE_RESULT=PASS" | tee -a "$R"
    exit 0
  fi

  if grep -q "RESULT: FAIL_REMOTE_AUTH" "$R"; then
    echo "PROMOTE_RESULT=REMOTE_AUTH_FAIL_BUT_CODE_OK" | tee -a "$R"
    echo "NOTE=Keeping promoted code because failure is remote auth, not compile/runtime syntax." | tee -a "$R"
    exit 0
  fi

  echo "PROMOTE_VERIFY_NOT_PASS -> rollback" | tee -a "$R"
  cp -p "$B" "$TARGET" || die "rollback failed"
  python -m py_compile "$TARGET" || die "rollback restored file but compile failed"
  echo "ROLLBACK_DONE=$B" | tee -a "$R"
  exit 1
}

cmd_rollback_latest() {
  need_target
  B="$(ls -1t "$BACKUPS"/s43_before_promote_*.py 2>/dev/null | head -1 || true)"
  [ -n "$B" ] || die "no rollback backup found in $BACKUPS"

  T="$(ts)"
  CURRENT="$BACKUPS/s43_before_manual_rollback_${T}.py"
  cp -p "$TARGET" "$CURRENT" || die "could not backup current before rollback"
  cp -p "$B" "$TARGET" || die "rollback copy failed"
  python -m py_compile "$TARGET" || die "rollback compile failed"

  echo "ROLLBACK_OK"
  echo "RESTORED_FROM=$B"
  echo "CURRENT_SAVED_AS=$CURRENT"
}

cmd_diff_latest() {
  need_target
  C="$(ls -1t "$CANDIDATES"/s43_candidate_*.py 2>/dev/null | head -1 || true)"
  [ -n "$C" ] || die "no candidate found"
  echo "LATEST_CANDIDATE=$C"
  diff -u "$TARGET" "$C" || true
}

cmd_help() {
  cat <<'EOF'
S43 SelfPatch - safe AI-assisted patch workflow

Commands:
  ./s43_selfpatch.sh status
  ./s43_selfpatch.sh new-candidate
  ./s43_selfpatch.sh check <candidate.py>
  ./s43_selfpatch.sh diff-latest
  ./s43_selfpatch.sh promote <candidate.py>
  ./s43_selfpatch.sh rollback-latest

Safe flow:
  1) ./s43_selfpatch.sh new-candidate
  2) nano candidates/s43_candidate_YYYYMMDD_HHMMSS.py
  3) ./s43_selfpatch.sh check candidates/s43_candidate_YYYYMMDD_HHMMSS.py
  4) ./s43_selfpatch.sh promote candidates/s43_candidate_YYYYMMDD_HHMMSS.py

Rules:
  - production s43.py is not touched until promote
  - backup is created before promote
  - compile is mandatory
  - toolkit verify is mandatory
  - rollback is automatic on unsafe failure
  - FAIL_REMOTE_AUTH is treated as remote/auth issue, not code failure
EOF
}

case "${1:-help}" in
  status) cmd_status ;;
  new-candidate) cmd_new_candidate ;;
  check) shift; cmd_check "$@" ;;
  promote) shift; cmd_promote "$@" ;;
  rollback-latest) cmd_rollback_latest ;;
  diff-latest) cmd_diff_latest ;;
  help|-h|--help) cmd_help ;;
  *) cmd_help; exit 1 ;;
esac
