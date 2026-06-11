#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

PROJECT_DIR="$HOME/s43_refactor"
TARGET="$PROJECT_DIR/s43.py"
cmd="${1:-verify}"

latest_file() {
  local pattern="$1"
  ls -1t $pattern 2>/dev/null | head -n 1 || true
}

do_verify() {
  local TS BACKUP LOGFILE SUMMARY RUN_RC
  local HAS_403 HAS_INVALID_TOKEN TOKEN_PRESENT AUTH_SCHEME
  local BALANCE_OK BALANCE_FAILED FINAL_STATUS SUMMARY_LINE

  TS="$(date +%Y%m%d_%H%M%S)"
  BACKUP="$PROJECT_DIR/s43_clean_compile_ok_${TS}.py"
  LOGFILE="$PROJECT_DIR/retry_after_exchange_fix_${TS}.log"
  SUMMARY="$PROJECT_DIR/s43_verify_summary_${TS}.txt"

  cd "$PROJECT_DIR"

  echo "========================================"
  echo " S43 TOOLKIT VERIFY"
  echo "========================================"
  echo "PROJECT_DIR=$PROJECT_DIR"
  echo "TARGET=$TARGET"
  echo "LOGFILE=$LOGFILE"
  echo "SUMMARY=$SUMMARY"
  echo "========================================"

  if [ ! -f "$TARGET" ]; then
    echo "ERROR: s43.py not found at: $TARGET"
    exit 1
  fi

  cp -f "$TARGET" "$BACKUP"
  echo "BACKUP_OK: $BACKUP"

  python -m py_compile "$TARGET"
  echo "COMPILE_OK"

  set +e
  python "$TARGET" 2>&1 | tee "$LOGFILE"
  RUN_RC=${PIPESTATUS[0]:-0}
  set -e

  echo "----------------------------------------"
  grep -n "403\|توکن نامعتبر\|token_present\|auth_scheme\|balance_ok\|balance_failed\|summary\|ISOCHK_GLOBAL" "$LOGFILE" || true
  echo "----------------------------------------"

  HAS_403=0
  HAS_INVALID_TOKEN=0
  TOKEN_PRESENT="unknown"
  AUTH_SCHEME="unknown"
  BALANCE_OK="unknown"
  BALANCE_FAILED="unknown"
  FINAL_STATUS="CHECK_LOG_REQUIRED"

  grep -q "HTTP 403" "$LOGFILE" && HAS_403=1 || true
  grep -q "توکن نامعتبر" "$LOGFILE" && HAS_INVALID_TOKEN=1 || true

  if grep -q "token_present=True" "$LOGFILE"; then
    TOKEN_PRESENT="True"
  elif grep -q "token_present=False" "$LOGFILE"; then
    TOKEN_PRESENT="False"
  fi

  if grep -q "auth_scheme=Token" "$LOGFILE"; then
    AUTH_SCHEME="Token"
  fi

  SUMMARY_LINE="$(grep "summary wallets=" "$LOGFILE" | tail -n 1 || true)"
  if [ -n "$SUMMARY_LINE" ]; then
    BALANCE_OK="$(printf '%s\n' "$SUMMARY_LINE" | sed -n 's/.*balance_ok=\([0-9][0-9]*\).*/\1/p')"
    BALANCE_FAILED="$(printf '%s\n' "$SUMMARY_LINE" | sed -n 's/.*balance_failed=\([0-9][0-9]*\).*/\1/p')"
  fi

  if [ "$HAS_403" = "1" ] && [ "$HAS_INVALID_TOKEN" = "1" ]; then
    FINAL_STATUS="API_403_INVALID_TOKEN"
  elif [ "$BALANCE_FAILED" = "0" ] && [ "$BALANCE_OK" != "unknown" ]; then
    FINAL_STATUS="BALANCE_ALL_OK"
  elif [ "$BALANCE_FAILED" != "unknown" ]; then
    FINAL_STATUS="PARTIAL_OR_TOTAL_BALANCE_FAILURE"
  fi

  {
    printf '%s\n' "S43_TOOLKIT_VERIFY"
    printf '%s\n' "timestamp=$TS"
    printf '%s\n' "run_rc=$RUN_RC"
    printf '%s\n' "backup=$BACKUP"
    printf '%s\n' "logfile=$LOGFILE"
    printf '%s\n' "compile_status=COMPILE_OK"
    printf '%s\n' "has_http_403=$HAS_403"
    printf '%s\n' "has_invalid_token_text=$HAS_INVALID_TOKEN"
    printf '%s\n' "token_present=$TOKEN_PRESENT"
    printf '%s\n' "auth_scheme=$AUTH_SCHEME"
    printf '%s\n' "balance_ok=$BALANCE_OK"
    printf '%s\n' "balance_failed=$BALANCE_FAILED"
    printf '%s\n' "final_status=$FINAL_STATUS"
  } > "$SUMMARY"

  echo "========================================"
  cat "$SUMMARY"
  echo "========================================"

  if [ "$FINAL_STATUS" = "API_403_INVALID_TOKEN" ]; then
    echo "RESULT: FAIL_REMOTE_AUTH"
  elif [ "$FINAL_STATUS" = "BALANCE_ALL_OK" ]; then
    echo "RESULT: PASS"
  else
    echo "RESULT: CHECK_LOG"
  fi

  echo "LOGFILE=$LOGFILE"
  echo "SUMMARY=$SUMMARY"
}

do_latest_log() {
  local f
  cd "$PROJECT_DIR"
  f="$(latest_file 'retry_after_exchange_fix_*.log')"
  if [ -z "$f" ]; then
    echo "ERROR: no log found"
    exit 1
  fi
  echo "LATEST_LOG=$f"
  tail -n 40 "$f"
}

do_latest_summary() {
  local f
  cd "$PROJECT_DIR"
  f="$(latest_file 's43_verify_summary_*.txt')"
  if [ -z "$f" ]; then
    echo "ERROR: no summary found"
    exit 1
  fi
  echo "LATEST_SUMMARY=$f"
  cat "$f"
}

do_list_backups() {
  cd "$PROJECT_DIR"
  ls -1t s43_clean_compile_ok_*.py 2>/dev/null || {
    echo "ERROR: no backups found"
    exit 1
  }
}

do_restore_latest() {
  local f
  cd "$PROJECT_DIR"
  f="$(latest_file 's43_clean_compile_ok_*.py')"
  if [ -z "$f" ]; then
    echo "ERROR: no backup found"
    exit 1
  fi
  cp -f "$f" "$TARGET"
  python -m py_compile "$TARGET"
  echo "RESTORE_OK: $f"
}

case "$cmd" in
  verify)
    do_verify
    ;;
  latest-log)
    do_latest_log
    ;;
  latest-summary)
    do_latest_summary
    ;;
  list-backups)
    do_list_backups
    ;;
  restore-latest)
    do_restore_latest
    ;;
  *)
    echo "Usage: $0 {verify|latest-log|latest-summary|list-backups|restore-latest}"
    exit 1
    ;;
esac
