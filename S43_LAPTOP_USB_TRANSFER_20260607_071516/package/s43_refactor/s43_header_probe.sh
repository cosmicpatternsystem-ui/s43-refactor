#!/usr/bin/env bash
set -u

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPORTS="$PROJECT_DIR/reports"
LOGS="$PROJECT_DIR/logs"

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
  for key in REAL_ARZ_TOKEN ACCESS_TOKEN API_TOKEN TOKEN ARZ_TOKEN ARZPLUS_TOKEN ARZ_PLUS_TOKEN S43_W1_TOKEN W1_TOKEN; do
    val="$(printenv "$key" 2>/dev/null || true)"
    if [ -n "${val:-}" ]; then
      echo "$key|$val"
      return 0
    fi
  done

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

normalize_base() {
  b="$1"
  b="${b%/}"
  printf "%s" "$b"
}

make_url() {
  base="$(normalize_base "$1")"
  path="$2"
  if [ "${path#/}" = "$path" ]; then
    path="/$path"
  fi
  printf "%s%s" "$base" "$path"
}

curl_probe() {
  label="$1"
  url="$2"
  header_name="$3"
  header_value="$4"

  tmp_body="$LOGS/header_probe_body_${STAMP}_${REQ_NO}.txt"
  tmp_hdr="$LOGS/header_probe_headers_${STAMP}_${REQ_NO}.txt"

  if [ "$header_name" = "__NO_AUTH__" ]; then
    code="$(
      curl -sS \
        --connect-timeout 10 \
        --max-time 25 \
        -D "$tmp_hdr" \
        -o "$tmp_body" \
        -w "%{http_code}" \
        "$url" 2>>"$CURL_ERR_LOG" || printf "000"
    )"
  else
    code="$(
      curl -sS \
        --connect-timeout 10 \
        --max-time 25 \
        -D "$tmp_hdr" \
        -o "$tmp_body" \
        -w "%{http_code}" \
        -H "$header_name: $header_value" \
        "$url" 2>>"$CURL_ERR_LOG" || printf "000"
    )"
  fi

  body_one_line="$(tr '\n\r' '  ' < "$tmp_body" 2>/dev/null | cut -c1-300 || true)"
  content_type="$(grep -i '^Content-Type:' "$tmp_hdr" 2>/dev/null | head -1 | sed 's/[[:space:]]*$//' || true)"
  location="$(grep -i '^Location:' "$tmp_hdr" 2>/dev/null | head -1 | sed 's/[[:space:]]*$//' || true)"

  {
    echo "----"
    echo "request_no=$REQ_NO"
    echo "label=$label"
    echo "url=$url"
    echo "auth_header=$header_name"
    echo "http_code=$code"
    [ -n "$content_type" ] && echo "$content_type"
    [ -n "$location" ] && echo "$location"
    echo "body_preview=$body_one_line"
  } | tee -a "$REPORT"

  echo "$REQ_NO|$label|$url|$header_name|$code|$body_one_line" >> "$MATRIX"

  REQ_NO=$((REQ_NO + 1))
}

build_base_candidates() {
  # User can override:
  #   export S43_PROBE_BASE_URL="https://..."
  if [ -n "${S43_PROBE_BASE_URL:-}" ]; then
    printf "%s\n" "$S43_PROBE_BASE_URL"
    return 0
  fi

  # Conservative candidates.
  # اگر base_url واقعی را می‌دانی، بهتر است S43_PROBE_BASE_URL را تنظیم کنی.
  cat <<'EOF'
https://arzplus.com
https://www.arzplus.com
https://api.arzplus.com
EOF
}

build_path_candidates() {
  # User can override:
  #   export S43_PROBE_PATH="/api/v1/balance"
  if [ -n "${S43_PROBE_PATH:-}" ]; then
    printf "%s\n" "$S43_PROBE_PATH"
    return 0
  fi

  # Balance/auth-related candidates.
  # ممکن است همه درست نباشند؛ هدف دیدن تفاوت پاسخ‌هاست.
  cat <<'EOF'
/api/v1/balance
/api/v1/balance/
/api/balance
/api/balance/
/api/v1/wallet/balance
/api/v1/wallet/balance/
/api/v1/wallets/balance
/api/v1/wallets/balance/
/api/v1/me
/api/v1/me/
/api/me
/api/me/
EOF
}

write_header() {
  {
    echo "S43_HEADER_PROBE_REPORT"
    echo "timestamp=$STAMP"
    echo "project_dir=$PROJECT_DIR"
    echo
    echo "source_hint=s43.py builds Authorization header as: <auth_scheme> <token>"
    echo "source_ref=s43.py lines 1967-1970 from previous retrieval"
    echo "scheme_ref=s43.py around lines 1067 and 1073 from previous retrieval"
    echo
  } | tee "$REPORT"
}

run_probe() {
  picked="$(pick_token || true)"
  PICKED_KEY="$(printf '%s' "$picked" | cut -d'|' -f1)"
  TOKEN_VAL="$(printf '%s' "$picked" | cut -d'|' -f2-)"

  {
    echo "== TOKEN SELECTION =="
  } | tee -a "$REPORT"

  if [ -z "${TOKEN_VAL:-}" ]; then
    {
      echo "picked_key="
      echo "picked_token=<empty>"
      echo "HEADER_PROBE_RESULT=MISSING_TOKEN"
      echo "ACTION=Export a valid token first, then rerun."
      echo "REPORT_SAVED=$REPORT"
    } | tee -a "$REPORT"
    exit 2
  fi

  {
    echo "picked_key=$PICKED_KEY"
    echo "picked_token=$(mask_value "$TOKEN_VAL")"
    echo "picked_token_fp=$(safe_hash "$TOKEN_VAL")"
    echo
    echo "== OVERRIDES =="
    echo "S43_PROBE_BASE_URL=${S43_PROBE_BASE_URL:-<not_set>}"
    echo "S43_PROBE_PATH=${S43_PROBE_PATH:-<not_set>}"
    echo
    echo "== PROBE MATRIX =="
  } | tee -a "$REPORT"

  REQ_NO=1

  while IFS= read -r base; do
    [ -n "$base" ] || continue

    while IFS= read -r path; do
      [ -n "$path" ] || continue

      url="$(make_url "$base" "$path")"

      # First: no auth, for baseline.
      curl_probe "NO_AUTH_BASELINE" "$url" "__NO_AUTH__" ""

      # Same style as s43.py currently uses.
      curl_probe "AUTHORIZATION_TOKEN" "$url" "Authorization" "Token $TOKEN_VAL"

      # Common alternatives.
      curl_probe "AUTHORIZATION_BEARER" "$url" "Authorization" "Bearer $TOKEN_VAL"
      curl_probe "AUTHORIZATION_RAW" "$url" "Authorization" "$TOKEN_VAL"
      curl_probe "X_API_KEY" "$url" "X-API-KEY" "$TOKEN_VAL"
      curl_probe "TOKEN_HEADER_LOWER" "$url" "token" "$TOKEN_VAL"

    done < <(build_path_candidates)

  done < <(build_base_candidates)
}

verdict() {
  {
    echo
    echo "== VERDICT =="
  } | tee -a "$REPORT"

  if [ ! -s "$MATRIX" ]; then
    {
      echo "HEADER_PROBE_RESULT=NO_MATRIX"
      echo "ACTION=No requests were recorded."
      echo "REPORT_SAVED=$REPORT"
    } | tee -a "$REPORT"
    return 0
  fi

  any_200="$(awk -F'|' '$5 ~ /^2/ {print; found=1} END{exit found?0:1}' "$MATRIX" 2>/dev/null || true)"
  any_401="$(awk -F'|' '$5 == "401" {print; found=1} END{exit found?0:1}' "$MATRIX" 2>/dev/null || true)"
  any_403="$(awk -F'|' '$5 == "403" {print; found=1} END{exit found?0:1}' "$MATRIX" 2>/dev/null || true)"
  any_404="$(awk -F'|' '$5 == "404" {print; found=1} END{exit found?0:1}' "$MATRIX" 2>/dev/null || true)"
  any_000="$(awk -F'|' '$5 == "000" {print; found=1} END{exit found?0:1}' "$MATRIX" 2>/dev/null || true)"

  bearer_2xx="$(awk -F'|' '$2 == "AUTHORIZATION_BEARER" && $5 ~ /^2/ {print; found=1} END{exit found?0:1}' "$MATRIX" 2>/dev/null || true)"
  token_2xx="$(awk -F'|' '$2 == "AUTHORIZATION_TOKEN" && $5 ~ /^2/ {print; found=1} END{exit found?0:1}' "$MATRIX" 2>/dev/null || true)"
  token_403_invalid="$(awk -F'|' '$2 == "AUTHORIZATION_TOKEN" && $5 == "403" && ($6 ~ /توکن نامعتبر/ || tolower($6) ~ /invalid/) {print; found=1} END{exit found?0:1}' "$MATRIX" 2>/dev/null || true)"
  bearer_403_invalid="$(awk -F'|' '$2 == "AUTHORIZATION_BEARER" && $5 == "403" && ($6 ~ /توکن نامعتبر/ || tolower($6) ~ /invalid/) {print; found=1} END{exit found?0:1}' "$MATRIX" 2>/dev/null || true)"

  echo "any_2xx_count=$(printf "%s\n" "$any_200" | grep -c . || true)" | tee -a "$REPORT"
  echo "any_401_count=$(printf "%s\n" "$any_401" | grep -c . || true)" | tee -a "$REPORT"
  echo "any_403_count=$(printf "%s\n" "$any_403" | grep -c . || true)" | tee -a "$REPORT"
  echo "any_404_count=$(printf "%s\n" "$any_404" | grep -c . || true)" | tee -a "$REPORT"
  echo "any_000_count=$(printf "%s\n" "$any_000" | grep -c . || true)" | tee -a "$REPORT"

  if [ -n "$token_2xx" ]; then
    {
      echo "HEADER_PROBE_RESULT=TOKEN_SCHEME_WORKS"
      echo "ACTION=Authorization: Token works directly. If s43.py still fails, inspect exact URL/path, token parsing, or runtime endpoint."
      echo "working_rows:"
      printf "%s\n" "$token_2xx"
    } | tee -a "$REPORT"

  elif [ -n "$bearer_2xx" ]; then
    {
      echo "HEADER_PROBE_RESULT=BEARER_SCHEME_WORKS"
      echo "ACTION=API accepted Authorization: Bearer. s43.py currently uses Token; next patch should allow auth_scheme=Bearer."
      echo "working_rows:"
      printf "%s\n" "$bearer_2xx"
    } | tee -a "$REPORT"

  elif [ -n "$any_200" ]; then
    {
      echo "HEADER_PROBE_RESULT=SOME_AUTH_OR_ENDPOINT_WORKS"
      echo "ACTION=At least one request returned 2xx. Inspect working_rows and align s43.py base_url/path/header."
      echo "working_rows:"
      printf "%s\n" "$any_200"
    } | tee -a "$REPORT"

  elif [ -n "$token_403_invalid" ] && [ -n "$bearer_403_invalid" ]; then
    {
      echo "HEADER_PROBE_RESULT=BOTH_TOKEN_AND_BEARER_INVALID"
      echo "ACTION=Both Token and Bearer produce invalid-token style 403. Most likely token/permission/IP whitelist/account status is wrong."
    } | tee -a "$REPORT"

  elif [ -n "$token_403_invalid" ]; then
    {
      echo "HEADER_PROBE_RESULT=TOKEN_SCHEME_INVALID_TOKEN"
      echo "ACTION=Current s43.py scheme reproduces invalid-token 403. If no other scheme works, regenerate/check token, permissions, whitelist, and endpoint."
    } | tee -a "$REPORT"

  elif [ -n "$any_404" ] && [ -z "$any_403" ]; then
    {
      echo "HEADER_PROBE_RESULT=ENDPOINT_NOT_FOUND_CANDIDATES"
      echo "ACTION=Candidate paths are likely wrong. Set S43_PROBE_BASE_URL and S43_PROBE_PATH to the exact API endpoint, then rerun."
    } | tee -a "$REPORT"

  elif [ -n "$any_000" ] && [ -z "$any_401" ] && [ -z "$any_403" ] && [ -z "$any_404" ]; then
    {
      echo "HEADER_PROBE_RESULT=NETWORK_OR_TLS_FAILURE"
      echo "ACTION=Check curl error log, DNS, TLS, internet access, or blocked host."
      echo "curl_err_log=$CURL_ERR_LOG"
    } | tee -a "$REPORT"

  else
    {
      echo "HEADER_PROBE_RESULT=NO_WORKING_COMBINATION"
      echo "ACTION=No tested combination worked. Need exact official base_url/path/header spec or regenerate/check token."
    } | tee -a "$REPORT"
  fi

  {
    echo
    echo "MATRIX_SAVED=$MATRIX"
    echo "CURL_ERR_LOG=$CURL_ERR_LOG"
    echo "REPORT_SAVED=$REPORT"
  } | tee -a "$REPORT"
}

cmd_run() {
  if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: curl not found. Install curl first."
    exit 1
  fi

  STAMP="$(ts)"
  REPORT="$REPORTS/header_probe_$STAMP.txt"
  MATRIX="$REPORTS/header_probe_matrix_$STAMP.tsv"
  CURL_ERR_LOG="$LOGS/header_probe_curl_err_$STAMP.log"

  write_header
  run_probe
  verdict
}

cmd_latest() {
  L="$(ls -1t "$REPORTS"/header_probe_*.txt 2>/dev/null | head -1 || true)"
  if [ -z "$L" ]; then
    echo "No header probe report found."
    exit 1
  fi
  echo "LATEST_HEADER_PROBE_REPORT=$L"
  cat "$L"
}

cmd_help() {
  cat <<'EOF'
S43 Header Probe

Commands:
  ./s43_header_probe.sh run
  ./s43_header_probe.sh latest
  ./s43_header_probe.sh help

Optional overrides:
  export S43_PROBE_BASE_URL="https://arzplus.com"
  export S43_PROBE_PATH="/api/v1/balance"

Purpose:
  - Directly test API auth headers with curl
  - Compare Token vs Bearer vs raw/custom headers
  - Separate scheme mismatch from invalid token/permission/whitelist issues
EOF
}

case "${1:-run}" in
  run) cmd_run ;;
  latest) cmd_latest ;;
  help|-h|--help) cmd_help ;;
  *) cmd_help; exit 1 ;;
esac
