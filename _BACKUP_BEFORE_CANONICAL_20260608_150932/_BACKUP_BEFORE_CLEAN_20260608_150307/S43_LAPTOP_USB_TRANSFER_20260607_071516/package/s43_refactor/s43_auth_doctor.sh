#!/usr/bin/env bash
set -u

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$PROJECT_DIR/s43.py"
TOOLKIT="$PROJECT_DIR/s43_toolkit.sh"
REPORTS="$PROJECT_DIR/reports"

mkdir -p "$REPORTS"

ts() {
  date +"%Y%m%d_%H%M%S"
}

mask_value() {
  v="${1:-}"
  n="${#v}"
  if [ "$n" -le 0 ]; then
    echo "<empty>"
  elif [ "$n" -le 6 ]; then
    echo "***"
  else
    first="$(printf "%s" "$v" | cut -c1-3)"
    last="$(printf "%s" "$v" | rev | cut -c1-3 | rev)"
    echo "${first}***${last} len=${n}"
  fi
}

latest_file() {
  pattern="$1"
  ls -1t $pattern 2>/dev/null | head -1 || true
}

write_header() {
  {
    echo "S43_AUTH_DOCTOR_REPORT"
    echo "timestamp=$(ts)"
    echo "project_dir=$PROJECT_DIR"
    echo "target=$TARGET"
    echo "toolkit=$TOOLKIT"
    echo
  } | tee "$REPORT"
}

check_files() {
  {
    echo "== FILE CHECK =="
    if [ -f "$TARGET" ]; then
      echo "s43.py=FOUND"
    else
      echo "s43.py=MISSING"
    fi

    if [ -x "$TOOLKIT" ]; then
      echo "s43_toolkit.sh=FOUND_EXECUTABLE"
    elif [ -f "$TOOLKIT" ]; then
      echo "s43_toolkit.sh=FOUND_NOT_EXECUTABLE"
    else
      echo "s43_toolkit.sh=MISSING"
    fi
    echo
  } | tee -a "$REPORT"
}

check_compile() {
  {
    echo "== COMPILE CHECK =="
  } | tee -a "$REPORT"

  if [ -f "$TARGET" ]; then
    if python -m py_compile "$TARGET" 2>>"$REPORT"; then
      echo "compile_status=COMPILE_OK" | tee -a "$REPORT"
    else
      echo "compile_status=COMPILE_FAIL" | tee -a "$REPORT"
    fi
  else
    echo "compile_status=SKIPPED_TARGET_MISSING" | tee -a "$REPORT"
  fi
  echo | tee -a "$REPORT"
}

find_latest_logs() {
  SUMMARY="$(latest_file "$PROJECT_DIR"/s43_verify_summary_*.txt)"
  LOG="$(latest_file "$PROJECT_DIR"/retry_after_exchange_fix_*.log)"

  # fallback: maybe toolkit/report directories
  if [ -z "$SUMMARY" ]; then
    SUMMARY="$(latest_file "$PROJECT_DIR"/summaries/*.txt)"
  fi
  if [ -z "$LOG" ]; then
    LOG="$(latest_file "$PROJECT_DIR"/logs/*.log)"
  fi

  {
    echo "== LATEST ARTIFACTS =="
    echo "latest_summary=${SUMMARY:-NONE}"
    echo "latest_log=${LOG:-NONE}"
    echo
  } | tee -a "$REPORT"
}

extract_summary() {
  {
    echo "== SUMMARY SIGNALS =="
    if [ -n "${SUMMARY:-}" ] && [ -f "$SUMMARY" ]; then
      grep -E "compile_status=|run_rc=|has_http_403=|has_invalid_token_text=|token_present=|auth_scheme=|balance_ok=|balance_failed=|final_status=|RESULT:" "$SUMMARY" 2>/dev/null || true
    else
      echo "summary_status=NOT_FOUND"
    fi
    echo
  } | tee -a "$REPORT"
}

extract_log() {
  {
    echo "== LOG SIGNALS =="
    if [ -n "${LOG:-}" ] && [ -f "$LOG" ]; then
      echo "-- 403 / invalid token lines --"
      grep -nE "HTTP 403|توکن نامعتبر|invalid token|Invalid token|token_present|auth_scheme|balance_ok|balance_failed|AUTHDBG|ISOCHK_GLOBAL|summary" "$LOG" 2>/dev/null | tail -80 || true
    else
      echo "log_status=NOT_FOUND"
    fi
    echo
  } | tee -a "$REPORT"
}

check_env_safely() {
  {
    echo "== ENV TOKEN/API/KEY CHECK MASKED =="
    echo "NOTE=Values are masked. No secret is printed."

    found=0
    env | sort | while IFS='=' read -r k v; do
      case "$k" in
        *TOKEN*|*Token*|*token*|*API*KEY*|*Api*Key*|*api*key*|*SECRET*|*Secret*|*secret*)
          found=1
          printf "%s=%s\n" "$k" "$(mask_value "$v")"
          ;;
      esac
    done

    echo
  } | tee -a "$REPORT"
}

run_toolkit_latest_if_available() {
  {
    echo "== TOOLKIT QUICK VIEW =="
  } | tee -a "$REPORT"

  if [ -x "$TOOLKIT" ]; then
    echo "-- latest-summary --" | tee -a "$REPORT"
    "$TOOLKIT" latest-summary 2>&1 | tail -80 | tee -a "$REPORT" || true
    echo | tee -a "$REPORT"

    echo "-- latest-log --" | tee -a "$REPORT"
    "$TOOLKIT" latest-log 2>&1 | tail -80 | tee -a "$REPORT" || true
  else
    echo "toolkit_quick_view=SKIPPED" | tee -a "$REPORT"
  fi
  echo | tee -a "$REPORT"
}

verdict() {
  HAS_403=0
  HAS_INVALID=0
  HAS_COMPILE_OK=0
  HAS_REMOTE_AUTH_RESULT=0

  if grep -q "HTTP 403" "$REPORT"; then HAS_403=1; fi
  if grep -q "توکن نامعتبر\|invalid token\|Invalid token" "$REPORT"; then HAS_INVALID=1; fi
  if grep -q "compile_status=COMPILE_OK\|COMPILE_OK" "$REPORT"; then HAS_COMPILE_OK=1; fi
  if grep -q "RESULT: FAIL_REMOTE_AUTH\|final_status=API_403_INVALID_TOKEN" "$REPORT"; then HAS_REMOTE_AUTH_RESULT=1; fi

  {
    echo "== VERDICT =="
    echo "has_http_403=$HAS_403"
    echo "has_invalid_token_text=$HAS_INVALID"
    echo "has_compile_ok=$HAS_COMPILE_OK"
    echo "has_remote_auth_result=$HAS_REMOTE_AUTH_RESULT"

    if [ "$HAS_COMPILE_OK" = "1" ] && { [ "$HAS_403" = "1" ] || [ "$HAS_INVALID" = "1" ] || [ "$HAS_REMOTE_AUTH_RESULT" = "1" ]; }; then
      echo "AUTH_DOCTOR_RESULT=REMOTE_AUTH_OR_TOKEN_PROBLEM"
      echo "ACTION=Do not patch s43.py for this. Regenerate/check token, permission, IP whitelist, endpoint/base_url, and auth scheme."
    elif [ "$HAS_COMPILE_OK" = "1" ]; then
      echo "AUTH_DOCTOR_RESULT=CODE_COMPILES_NO_REMOTE_AUTH_PROOF_IN_LATEST_ARTIFACTS"
      echo "ACTION=Run ./s43_toolkit.sh verify then run this doctor again."
    else
      echo "AUTH_DOCTOR_RESULT=NEEDS_MANUAL_CHECK"
      echo "ACTION=Check compile/log/toolkit availability."
    fi

    echo
    echo "REPORT_SAVED=$REPORT"
  } | tee -a "$REPORT"
}

cmd_doctor() {
  REPORT="$REPORTS/auth_doctor_$(ts).txt"
  write_header
  check_files
  check_compile
  find_latest_logs
  extract_summary
  extract_log
  check_env_safely
  run_toolkit_latest_if_available
  verdict
}

cmd_latest() {
  L="$(ls -1t "$REPORTS"/auth_doctor_*.txt 2>/dev/null | head -1 || true)"
  if [ -z "$L" ]; then
    echo "No auth doctor report found."
    exit 1
  fi
  echo "LATEST_AUTH_DOCTOR_REPORT=$L"
  cat "$L"
}

cmd_help() {
  cat <<'EOF'
S43 Auth Doctor

Commands:
  ./s43_auth_doctor.sh doctor
  ./s43_auth_doctor.sh latest
  ./s43_auth_doctor.sh help

Purpose:
  - diagnose HTTP 403 / invalid token condition
  - never edits s43.py
  - never prints raw secrets
  - stores report in reports/auth_doctor_YYYYMMDD_HHMMSS.txt
EOF
}

case "${1:-doctor}" in
  doctor) cmd_doctor ;;
  latest) cmd_latest ;;
  help|-h|--help) cmd_help ;;
  *) cmd_help; exit 1 ;;
esac
