#!/usr/bin/env bash
set -u

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPORTS="$PROJECT_DIR/reports"
LOGS="$PROJECT_DIR/logs"
TOOLKIT="$PROJECT_DIR/s43_toolkit.sh"

mkdir -p "$REPORTS" "$LOGS"

ts() {
  date +"%Y%m%d_%H%M%S"
}

mask_value() {
  v="${1:-}"
  n="${#v}"
  if [ "$n" -le 0 ]; then
    echo "<empty>"
  elif [ "$n" -le 6 ]; then
    echo "*** len=${n}"
  else
    first="$(printf "%s" "$v" | cut -c1-3)"
    last="$(printf "%s" "$v" | rev | cut -c1-3 | rev)"
    echo "${first}***${last} len=${n}"
  fi
}

safe_hash() {
  v="${1:-}"
  if command -v sha256sum >/dev/null 2>&1; then
    printf "%s" "$v" | sha256sum | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    printf "%s" "$v" | shasum -a 256 | awk '{print $1}'
  else
    printf "%s" "$v" | cksum | awk '{print $1}'
  fi
}

pick_token() {
  # priority order: stable/canonical vars first
  for key in REAL_ARZ_TOKEN ACCESS_TOKEN API_TOKEN TOKEN ARZ_TOKEN ARZPLUS_TOKEN ARZ_PLUS_TOKEN S43_W1_TOKEN W1_TOKEN; do
    val="$(printenv "$key" 2>/dev/null || true)"
    if [ -n "${val:-}" ]; then
      echo "$key|$val"
      return 0
    fi
  done

  # fallback: wallet-style vars
  for key in TOKEN_1 ARZ_TOKEN_1 ARZPLUS_TOKEN_1 ARZ_PLUS_TOKEN_1 WALLET_1_TOKEN; do
    val="$(printenv "$key" 2>/dev/null || true)"
    if [ -n "${val:-}" ]; then
      echo "$key|$val"
      return 0
    fi
  done

  echo "|"
  return 1
}

latest_summary_file() {
  ls -1t "$PROJECT_DIR"/s43_verify_summary_*.txt 2>/dev/null | head -1 || true
}

latest_log_file() {
  ls -1t "$PROJECT_DIR"/retry_after_exchange_fix_*.log "$LOGS"/*.log 2>/dev/null | head -1 || true
}

extract_signal_from_file() {
  f="$1"
  [ -f "$f" ] || return 0

  grep -E \
    'compile_status=|run_rc=|token_present=|auth_scheme=|HTTP 403|توکن نامعتبر|balance_ok=|balance_failed=|final_status=|RESULT:|FAIL_REMOTE_AUTH|API_403_INVALID_TOKEN|REMOTE_AUTH' \
    "$f" 2>/dev/null | tail -80 || true
}

write_report_header() {
  {
    echo "S43_ENV_CLEANROOM_REPORT"
    echo "timestamp=$STAMP"
    echo "project_dir=$PROJECT_DIR"
    echo "toolkit=$TOOLKIT"
    echo
  } | tee "$REPORT"
}

show_current_conflict_snapshot() {
  {
    echo "== CURRENT ENV SNAPSHOT (MASKED, SELECTED) =="
  } | tee -a "$REPORT"

  for key in \
    REAL_ARZ_TOKEN ACCESS_TOKEN API_TOKEN TOKEN ARZ_TOKEN ARZPLUS_TOKEN ARZ_PLUS_TOKEN S43_W1_TOKEN W1_TOKEN \
    TOKEN_1 TOKEN_2 TOKEN_3 ARZ_TOKEN_1 ARZ_TOKEN_2 ARZ_TOKEN_3 \
    ARZPLUS_TOKEN_1 ARZPLUS_TOKEN_2 ARZPLUS_TOKEN_3 \
    ARZ_PLUS_TOKEN_1 ARZ_PLUS_TOKEN_2 ARZ_PLUS_TOKEN_3 \
    WALLET_1_TOKEN WALLET_2_TOKEN WALLET_3_TOKEN \
    ARZPLUS_TOKEN1 ARZPLUS_TOKEN2 ARZPLUS_TOKEN3; do

    val="$(printenv "$key" 2>/dev/null || true)"
    if [ -n "${val:-}" ]; then
      echo "$key=$(mask_value "$val") fp=$(safe_hash "$val")"
    fi
  done | tee -a "$REPORT"

  echo | tee -a "$REPORT"
}

run_cleanroom_verify() {
  picked="$(pick_token || true)"
  PICKED_KEY="$(printf '%s' "$picked" | cut -d'|' -f1)"
  PICKED_TOKEN="$(printf '%s' "$picked" | cut -d'|' -f2-)"

  {
    echo "== CLEANROOM TOKEN SELECTION =="
  } | tee -a "$REPORT"

  if [ -z "${PICKED_TOKEN:-}" ]; then
    {
      echo "picked_key="
      echo "picked_token=<empty>"
      echo "CLEANROOM_RESULT=CLEANROOM_MISSING_TOKEN"
      echo "ACTION=No canonical token found in current env. Export one valid token first, then rerun."
      echo
      echo "REPORT_SAVED=$REPORT"
    } | tee -a "$REPORT"
    exit 2
  fi

  {
    echo "picked_key=$PICKED_KEY"
    echo "picked_token=$(mask_value "$PICKED_TOKEN")"
    echo "picked_token_fp=$(safe_hash "$PICKED_TOKEN")"
    echo
    echo "== CLEANROOM EXECUTION =="
    echo "mode=env -i with minimal variables"
    echo "canonical_vars_exported=TOKEN API_TOKEN ACCESS_TOKEN ARZ_TOKEN ARZPLUS_TOKEN ARZ_PLUS_TOKEN REAL_ARZ_TOKEN S43_W1_TOKEN W1_TOKEN TOKEN_1 TOKEN_2 TOKEN_3"
    echo "wallet_2_token_policy=not_exported_as_WALLET_2_TOKEN"
    echo
  } | tee -a "$REPORT"

  CLEAN_LOG="$LOGS/cleanroom_verify_$STAMP.log"

  # Important:
  # - env -i removes polluted shell env.
  # - We intentionally set many canonical names to the same selected token
  #   because s43.py may read different aliases.
  # - We do NOT export WALLET_2_TOKEN, WALLET_3_TOKEN, ARZPLUS_TOKEN1/2/3, OPENAI keys, etc.
  env -i \
    HOME="${HOME:-$PROJECT_DIR}" \
    USER="${USER:-u0_a}" \
    SHELL="${SHELL:-/data/data/com.termux/files/usr/bin/bash}" \
    TERM="${TERM:-xterm-256color}" \
    LANG="${LANG:-C.UTF-8}" \
    LC_ALL="${LC_ALL:-C.UTF-8}" \
    PATH="${PATH:-/data/data/com.termux/files/usr/bin:/system/bin:/system/xbin}" \
    PYTHONUNBUFFERED=1 \
    S43_SAFE_MODE=1 \
    S43_NO_TRADE=1 \
    TOKEN="$PICKED_TOKEN" \
    API_TOKEN="$PICKED_TOKEN" \
    ACCESS_TOKEN="$PICKED_TOKEN" \
    REAL_ARZ_TOKEN="$PICKED_TOKEN" \
    ARZ_TOKEN="$PICKED_TOKEN" \
    ARZPLUS_TOKEN="$PICKED_TOKEN" \
    ARZ_PLUS_TOKEN="$PICKED_TOKEN" \
    S43_W1_TOKEN="$PICKED_TOKEN" \
    W1_TOKEN="$PICKED_TOKEN" \
    TOKEN_1="$PICKED_TOKEN" \
    TOKEN_2="$PICKED_TOKEN" \
    TOKEN_3="$PICKED_TOKEN" \
    ARZ_TOKEN_1="$PICKED_TOKEN" \
    ARZ_TOKEN_2="$PICKED_TOKEN" \
    ARZ_TOKEN_3="$PICKED_TOKEN" \
    ARZPLUS_TOKEN_1="$PICKED_TOKEN" \
    ARZPLUS_TOKEN_2="$PICKED_TOKEN" \
    ARZPLUS_TOKEN_3="$PICKED_TOKEN" \
    ARZ_PLUS_TOKEN_1="$PICKED_TOKEN" \
    ARZ_PLUS_TOKEN_2="$PICKED_TOKEN" \
    ARZ_PLUS_TOKEN_3="$PICKED_TOKEN" \
    "$TOOLKIT" verify > "$CLEAN_LOG" 2>&1

  CLEAN_RC=$?

  {
    echo "cleanroom_run_rc=$CLEAN_RC"
    echo "cleanroom_log=$CLEAN_LOG"
    echo
    echo "== CLEANROOM LOG SIGNALS =="
  } | tee -a "$REPORT"

  extract_signal_from_file "$CLEAN_LOG" | tee -a "$REPORT"

  echo | tee -a "$REPORT"

  NEW_SUMMARY="$(latest_summary_file)"
  {
    echo "latest_summary_after_cleanroom=$NEW_SUMMARY"
    echo "== LATEST SUMMARY SIGNALS =="
  } | tee -a "$REPORT"

  if [ -n "$NEW_SUMMARY" ]; then
    extract_signal_from_file "$NEW_SUMMARY" | tee -a "$REPORT"
  else
    echo "No summary found after cleanroom verify." | tee -a "$REPORT"
  fi

  echo | tee -a "$REPORT"
}

verdict() {
  {
    echo "== VERDICT =="
  } | tee -a "$REPORT"

  HAS_403=0
  HAS_INVALID=0
  HAS_REMOTE_FAIL=0
  HAS_COMPILE_OK=0
  HAS_TOKEN_PRESENT=0

  if grep -q 'HTTP 403' "$REPORT" 2>/dev/null; then HAS_403=1; fi
  if grep -q 'توکن نامعتبر' "$REPORT" 2>/dev/null; then HAS_INVALID=1; fi
  if grep -Eq 'FAIL_REMOTE_AUTH|API_403_INVALID_TOKEN|REMOTE_AUTH' "$REPORT" 2>/dev/null; then HAS_REMOTE_FAIL=1; fi
  if grep -q 'COMPILE_OK\|compile_status=COMPILE_OK' "$REPORT" 2>/dev/null; then HAS_COMPILE_OK=1; fi
  if grep -q 'token_present=True' "$REPORT" 2>/dev/null; then HAS_TOKEN_PRESENT=1; fi

  echo "has_http_403=$HAS_403" | tee -a "$REPORT"
  echo "has_invalid_token_text=$HAS_INVALID" | tee -a "$REPORT"
  echo "has_remote_auth_fail=$HAS_REMOTE_FAIL" | tee -a "$REPORT"
  echo "has_compile_ok=$HAS_COMPILE_OK" | tee -a "$REPORT"
  echo "has_token_present=$HAS_TOKEN_PRESENT" | tee -a "$REPORT"

  if [ "$HAS_403" -eq 1 ] && [ "$HAS_INVALID" -eq 1 ]; then
    {
      echo "CLEANROOM_RESULT=CLEANROOM_STILL_403_INVALID_TOKEN"
      echo "ACTION=Even with a clean minimal env, API rejects the selected token. Regenerate/check token, permission, IP whitelist, base_url/endpoint, and auth scheme."
    } | tee -a "$REPORT"
  elif [ "$HAS_REMOTE_FAIL" -eq 1 ]; then
    {
      echo "CLEANROOM_RESULT=CLEANROOM_STILL_REMOTE_AUTH_FAIL"
      echo "ACTION=Clean env did not fix remote auth. Continue with header/base_url probe."
    } | tee -a "$REPORT"
  elif [ "$CLEAN_RC" -ne 0 ]; then
    {
      echo "CLEANROOM_RESULT=CLEANROOM_RUNTIME_CHANGED_OR_FAILED"
      echo "ACTION=Behavior changed under clean env. Inspect cleanroom_log for missing non-token env dependencies."
    } | tee -a "$REPORT"
  else
    {
      echo "CLEANROOM_RESULT=CLEANROOM_CHANGED_BEHAVIOR_OR_AUTH_FIXED"
      echo "ACTION=Clean env changed the result. The previous shell env likely had token precedence/conflict issues."
    } | tee -a "$REPORT"
  fi

  {
    echo
    echo "REPORT_SAVED=$REPORT"
  } | tee -a "$REPORT"
}

cmd_run() {
  if [ ! -x "$TOOLKIT" ]; then
    echo "ERROR: toolkit not executable or not found: $TOOLKIT"
    exit 1
  fi

  STAMP="$(ts)"
  REPORT="$REPORTS/env_cleanroom_$STAMP.txt"

  write_report_header
  show_current_conflict_snapshot
  run_cleanroom_verify
  verdict
}

cmd_latest() {
  L="$(ls -1t "$REPORTS"/env_cleanroom_*.txt 2>/dev/null | head -1 || true)"
  if [ -z "$L" ]; then
    echo "No cleanroom report found."
    exit 1
  fi
  echo "LATEST_ENV_CLEANROOM_REPORT=$L"
  cat "$L"
}

cmd_help() {
  cat <<'EOF'
S43 Env Cleanroom

Commands:
  ./s43_env_cleanroom.sh run
  ./s43_env_cleanroom.sh latest
  ./s43_env_cleanroom.sh help

Purpose:
  - run s43_toolkit.sh verify inside a minimal clean env
  - export only one selected canonical token through common aliases
  - avoid polluted/conflicting wallet token env vars
  - determine whether 403 is caused by env conflict or real remote token rejection
EOF
}

case "${1:-run}" in
  run) cmd_run ;;
  latest) cmd_latest ;;
  help|-h|--help) cmd_help ;;
  *) cmd_help; exit 1 ;;
esac
