#!/usr/bin/env bash
set -u

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
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
    # fallback weak fingerprint only for grouping, not security
    printf "%s" "$v" | cksum | awk '{print $1}'
  fi
}

collect_env_lines() {
  env | sort | while IFS='=' read -r k v; do
    case "$k" in
      *TOKEN*|*Token*|*token*|*SECRET*|*Secret*|*secret*|*API*KEY*|*Api*Key*|*api*key*)
        printf '%s=%s\n' "$k" "$v"
        ;;
    esac
  done
}

write_header() {
  {
    echo "S43_ENV_CHECK_REPORT"
    echo "timestamp=$(ts)"
    echo "project_dir=$PROJECT_DIR"
    echo
  } | tee "$REPORT"
}

section_all_vars() {
  {
    echo "== ALL MATCHING ENV VARS (MASKED) =="
  } | tee -a "$REPORT"

  COUNT_ALL=0
  while IFS='=' read -r k v; do
    [ -n "${k:-}" ] || continue
    COUNT_ALL=$((COUNT_ALL + 1))
    printf '%s=%s\n' "$k" "$(mask_value "$v")"
  done < <(collect_env_lines) | tee -a "$REPORT"

  {
    echo
    echo "all_matching_var_count=$COUNT_ALL"
    echo
  } | tee -a "$REPORT"
}

section_unique_values() {
  TMP_UNIQ="$REPORTS/.envcheck_unique_$$.tmp"
  : > "$TMP_UNIQ"

  while IFS='=' read -r k v; do
    [ -n "${k:-}" ] || continue
    fp="$(safe_hash "$v")"
    masked="$(mask_value "$v")"
    printf '%s|%s|%s\n' "$fp" "$k" "$masked" >> "$TMP_UNIQ"
  done < <(collect_env_lines)

  {
    echo "== UNIQUE VALUE GROUPS =="
  } | tee -a "$REPORT"

  if [ ! -s "$TMP_UNIQ" ]; then
    echo "unique_value_groups=0" | tee -a "$REPORT"
    echo | tee -a "$REPORT"
    rm -f "$TMP_UNIQ"
    return
  fi

  UNIQUE_GROUPS=0
  cut -d'|' -f1 "$TMP_UNIQ" | sort | uniq | while read -r fp; do
    [ -n "$fp" ] || continue
    UNIQUE_GROUPS=$((UNIQUE_GROUPS + 1))
    echo "fingerprint=$fp" 
    grep "^$fp|" "$TMP_UNIQ" | while IFS='|' read -r _ k masked; do
      echo "  var=$k value=$masked"
    done
  done | tee -a "$REPORT"

  UNIQUE_COUNT="$(cut -d'|' -f1 "$TMP_UNIQ" | sort | uniq | wc -l | tr -d ' ')"
  {
    echo
    echo "unique_value_groups=$UNIQUE_COUNT"
    echo
  } | tee -a "$REPORT"

  rm -f "$TMP_UNIQ"
}

section_priority_vars() {
  {
    echo "== PRIORITY / WALLET VARS =="
  } | tee -a "$REPORT"

  PRIORITY_KEYS="
TOKEN
API_TOKEN
ACCESS_TOKEN
REAL_ARZ_TOKEN
ARZ_TOKEN
ARZPLUS_TOKEN
ARZ_PLUS_TOKEN
S43_W1_TOKEN
W1_TOKEN
TOKEN_1
TOKEN_2
TOKEN_3
ARZ_TOKEN_1
ARZ_TOKEN_2
ARZ_TOKEN_3
ARZPLUS_TOKEN_1
ARZPLUS_TOKEN_2
ARZPLUS_TOKEN_3
ARZ_PLUS_TOKEN_1
ARZ_PLUS_TOKEN_2
ARZ_PLUS_TOKEN_3
WALLET_1_TOKEN
WALLET_2_TOKEN
WALLET_3_TOKEN
"

  FOUND_ANY=0
  for key in $PRIORITY_KEYS; do
    val="$(printenv "$key" 2>/dev/null || true)"
    if [ -n "${val:-}" ]; then
      FOUND_ANY=1
      echo "$key=$(mask_value "$val")"
    fi
  done | tee -a "$REPORT"

  if [ "$FOUND_ANY" -eq 0 ]; then
    echo "priority_vars=NONE_FOUND" | tee -a "$REPORT"
  fi

  echo | tee -a "$REPORT"
}

section_conflict_analysis() {
  {
    echo "== CONFLICT ANALYSIS =="
  } | tee -a "$REPORT"

  get_fp() {
    vv="$(printenv "$1" 2>/dev/null || true)"
    if [ -n "${vv:-}" ]; then
      safe_hash "$vv"
    else
      echo ""
    fi
  }

  BASE_KEYS="TOKEN API_TOKEN ACCESS_TOKEN REAL_ARZ_TOKEN ARZ_TOKEN ARZPLUS_TOKEN ARZ_PLUS_TOKEN S43_W1_TOKEN W1_TOKEN"
  WALLET_KEYS="TOKEN_1 TOKEN_2 TOKEN_3 ARZ_TOKEN_1 ARZ_TOKEN_2 ARZ_TOKEN_3 ARZPLUS_TOKEN_1 ARZPLUS_TOKEN_2 ARZPLUS_TOKEN_3 ARZ_PLUS_TOKEN_1 ARZ_PLUS_TOKEN_2 ARZ_PLUS_TOKEN_3 WALLET_1_TOKEN WALLET_2_TOKEN WALLET_3_TOKEN"

  BASE_TMP="$REPORTS/.envcheck_base_$$.tmp"
  W_TMP="$REPORTS/.envcheck_wallet_$$.tmp"
  : > "$BASE_TMP"
  : > "$W_TMP"

  for key in $BASE_KEYS; do
    val="$(printenv "$key" 2>/dev/null || true)"
    if [ -n "${val:-}" ]; then
      printf '%s|%s|%s\n' "$(safe_hash "$val")" "$key" "$(mask_value "$val")" >> "$BASE_TMP"
    fi
  done

  for key in $WALLET_KEYS; do
    val="$(printenv "$key" 2>/dev/null || true)"
    if [ -n "${val:-}" ]; then
      printf '%s|%s|%s\n' "$(safe_hash "$val")" "$key" "$(mask_value "$val")" >> "$W_TMP"
    fi
  done

  BASE_UNIQ=0
  W_UNIQ=0

  if [ -s "$BASE_TMP" ]; then
    BASE_UNIQ="$(cut -d'|' -f1 "$BASE_TMP" | sort | uniq | wc -l | tr -d ' ')"
  fi
  if [ -s "$W_TMP" ]; then
    W_UNIQ="$(cut -d'|' -f1 "$W_TMP" | sort | uniq | wc -l | tr -d ' ')"
  fi

  echo "base_group_unique_count=$BASE_UNIQ" | tee -a "$REPORT"
  echo "wallet_group_unique_count=$W_UNIQ" | tee -a "$REPORT"

  if [ -s "$BASE_TMP" ]; then
    echo "-- base group --" | tee -a "$REPORT"
    cat "$BASE_TMP" | while IFS='|' read -r fp k masked; do
      echo "  $k => $masked fp=$fp"
    done | tee -a "$REPORT"
  fi

  if [ -s "$W_TMP" ]; then
    echo "-- wallet group --" | tee -a "$REPORT"
    cat "$W_TMP" | while IFS='|' read -r fp k masked; do
      echo "  $k => $masked fp=$fp"
    done | tee -a "$REPORT"
  fi

  CONFLICT=0
  if [ "$BASE_UNIQ" -gt 1 ]; then CONFLICT=1; fi
  if [ "$W_UNIQ" -gt 1 ]; then CONFLICT=1; fi

  echo "env_conflict_detected=$CONFLICT" | tee -a "$REPORT"
  echo | tee -a "$REPORT"

  rm -f "$BASE_TMP" "$W_TMP"
}

section_verdict() {
  ALL_COUNT="$(env | grep -E 'TOKEN|Token|token|SECRET|Secret|secret|API.?KEY|Api.?Key|api.?key' | wc -l | tr -d ' ')"

  TMP_ALL="$REPORTS/.envcheck_all_$$.tmp"
  : > "$TMP_ALL"
  while IFS='=' read -r k v; do
    [ -n "${k:-}" ] || continue
    printf '%s\n' "$(safe_hash "$v")" >> "$TMP_ALL"
  done < <(collect_env_lines)

  UNIQUE_ALL=0
  if [ -s "$TMP_ALL" ]; then
    UNIQUE_ALL="$(sort "$TMP_ALL" | uniq | wc -l | tr -d ' ')"
  fi

  {
    echo "== VERDICT =="
    echo "matching_env_var_count=$ALL_COUNT"
    echo "unique_secret_value_count=$UNIQUE_ALL"
  } | tee -a "$REPORT"

  if [ "$ALL_COUNT" -eq 0 ]; then
    {
      echo "ENV_CHECK_RESULT=MISSING_EXPECTED_ENV"
      echo "ACTION=No matching token/key env vars found in current shell. Load env and rerun."
    } | tee -a "$REPORT"
  elif [ "$UNIQUE_ALL" -eq 1 ]; then
    {
      echo "ENV_CHECK_RESULT=LIKELY_SINGLE_TOKEN_BUT_REMOTE_REJECTED"
      echo "ACTION=Env looks consistent; investigate token validity, permission, IP whitelist, endpoint/base_url, and auth scheme."
    } | tee -a "$REPORT"
  elif [ "$UNIQUE_ALL" -gt 1 ] && [ "$UNIQUE_ALL" -le 3 ]; then
    {
      echo "ENV_CHECK_RESULT=MULTIPLE_TOKENS_PRESENT"
      echo "ACTION=There are multiple distinct secret values. Confirm which env var s43.py actually reads and remove ambiguity."
    } | tee -a "$REPORT"
  else
    {
      echo "ENV_CHECK_RESULT=ENV_CONFLICT_DETECTED"
      echo "ACTION=Many distinct secret values are present. Reduce env ambiguity, standardize token naming, and verify wallet-specific mapping."
    } | tee -a "$REPORT"
  fi

  {
    echo
    echo "REPORT_SAVED=$REPORT"
  } | tee -a "$REPORT"

  rm -f "$TMP_ALL"
}

cmd_check() {
  REPORT="$REPORTS/env_check_$(ts).txt"
  write_header
  section_all_vars
  section_unique_values
  section_priority_vars
  section_conflict_analysis
  section_verdict
}

cmd_latest() {
  L="$(ls -1t "$REPORTS"/env_check_*.txt 2>/dev/null | head -1 || true)"
  if [ -z "$L" ]; then
    echo "No env check report found."
    exit 1
  fi
  echo "LATEST_ENV_CHECK_REPORT=$L"
  cat "$L"
}

cmd_help() {
  cat <<'EOF'
S43 Env Check

Commands:
  ./s43_env_check.sh check
  ./s43_env_check.sh latest
  ./s43_env_check.sh help

Purpose:
  - inspect token/key/secret env vars safely
  - mask values
  - group identical values by fingerprint
  - detect multiple distinct token values / conflicts
  - save report into reports/env_check_YYYYMMDD_HHMMSS.txt
EOF
}

case "${1:-check}" in
  check) cmd_check ;;
  latest) cmd_latest ;;
  help|-h|--help) cmd_help ;;
  *) cmd_help; exit 1 ;;
esac
