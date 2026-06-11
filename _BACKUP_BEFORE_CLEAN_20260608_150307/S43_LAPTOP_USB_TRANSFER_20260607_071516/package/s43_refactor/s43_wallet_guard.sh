#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

CONFIG_DIR="$ROOT_DIR/config"
REGISTRY="$CONFIG_DIR/s43_wallet_registry.env"
REPORT_DIR="$ROOT_DIR/reports"

mkdir -p "$CONFIG_DIR" "$REPORT_DIR"
chmod 700 "$CONFIG_DIR" "$REPORT_DIR" 2>/dev/null || true

if [ -f "$REGISTRY" ]; then
  # shellcheck disable=SC1090
  source "$REGISTRY"
fi

mask_token() {
  local v="${1:-}"
  local n="${#v}"
  if [ "$n" -le 8 ]; then
    printf '%s' 'MASKED'
    return
  fi
  printf '%s...%s' "${v:0:4}" "${v:$((n-4)):4}"
}

fp_token() {
  local v="${1:-}"
  if [ -z "$v" ]; then
    printf '%s' 'NONE'
    return
  fi
  printf '%s' "$v" | sha256sum | awk '{print substr($1,1,16)}'
}

days_left_py() {
  python3 - "$1" <<'PY'
import sys
from datetime import datetime, date

s = sys.argv[1].strip()
if not s:
    print("")
    raise SystemExit(0)

try:
    d = datetime.strptime(s, "%Y-%m-%d").date()
    print((d - date.today()).days)
except Exception:
    print("INVALID")
PY
}

expiry_state() {
  local expires_at="${1:-}"
  local warn_days="${2:-7}"
  local dl
  dl="$(days_left_py "$expires_at")"

  if [ -z "$expires_at" ]; then
    printf '%s' 'UNKNOWN'
    return
  fi
  if [ "$dl" = "INVALID" ]; then
    printf '%s' 'INVALID_DATE'
    return
  fi
  if [ "$dl" -le 0 ]; then
    printf '%s' 'EXPIRED'
    return
  fi
  if [ "$dl" -le "$warn_days" ]; then
    printf '%s' 'WARNING'
    return
  fi
  printf '%s' 'OK'
}

write_wallet_block() {
  local wallet_id="$1"
  local label_var="ARZPLUS_WALLET_${wallet_id}_LABEL"
  local role_var="ARZPLUS_WALLET_${wallet_id}_ROLE"
  local token_var="ARZPLUS_WALLET_${wallet_id}_TOKEN"
  local reg_var="ARZPLUS_WALLET_${wallet_id}_REGISTERED_AT"
  local exp_var="ARZPLUS_WALLET_${wallet_id}_EXPIRES_AT"
  local warn_var="ARZPLUS_WALLET_${wallet_id}_WARN_DAYS"
  local status_var="ARZPLUS_WALLET_${wallet_id}_STATUS"

  local label="${!label_var:-}"
  local role="${!role_var:-}"
  local token="${!token_var:-}"
  local registered_at="${!reg_var:-}"
  local expires_at="${!exp_var:-}"
  local warn_days="${!warn_var:-7}"
  local status="${!status_var:-undefined}"

  local token_present="NO"
  [ -n "$token" ] && token_present="YES"

  local token_masked="NONE"
  [ -n "$token" ] && token_masked="$(mask_token "$token")"

  local token_fp="NONE"
  [ -n "$token" ] && token_fp="$(fp_token "$token")"

  local dl
  dl="$(days_left_py "$expires_at")"

  local exp_state
  exp_state="$(expiry_state "$expires_at" "$warn_days")"

  cat <<BLOCK
wallet_id=$wallet_id
label=$label
role=$role
status=$status
token_present=$token_present
token_masked=$token_masked
token_fp=$token_fp
registered_at=$registered_at
token_expires_at=$expires_at
warn_days=$warn_days
days_left=$dl
expiry_state=$exp_state

BLOCK
}

cmd_check() {
  local report="$REPORT_DIR/wallet_guard_$(date +%Y%m%d_%H%M%S).txt"
  {
    echo "== S43 WALLET GUARD REPORT =="
    echo "generated_at=$(date +%F' '%T)"
    echo

    write_wallet_block 1
    write_wallet_block 2
    write_wallet_block 3

    echo "== VERDICT =="
    echo "WALLET_GUARD_RESULT=CHECK_COMPLETE"
    echo "REPORT_SAVED=$report"
  } | tee "$report"
}

cmd_use() {
  local wallet_id="${1:-}"
  if [ -z "$wallet_id" ]; then
    echo "ERROR: wallet id required"
    exit 1
  fi

  local token_var="ARZPLUS_WALLET_${wallet_id}_TOKEN"
  local label_var="ARZPLUS_WALLET_${wallet_id}_LABEL"
  local role_var="ARZPLUS_WALLET_${wallet_id}_ROLE"
  local exp_var="ARZPLUS_WALLET_${wallet_id}_EXPIRES_AT"
  local warn_var="ARZPLUS_WALLET_${wallet_id}_WARN_DAYS"

  local token="${!token_var:-}"
  local label="${!label_var:-}"
  local role="${!role_var:-}"
  local expires_at="${!exp_var:-}"
  local warn_days="${!warn_var:-7}"

  if [ -z "$token" ]; then
    echo "ERROR: wallet token missing for wallet_id=$wallet_id"
    exit 1
  fi

  local runtime_env="$REPORT_DIR/s43_runtime_wallet_${wallet_id}_$(date +%Y%m%d_%H%M%S).env"

  cat > "$runtime_env" <<RUNTIME
export S43_ACTIVE_WALLET="$wallet_id"
export S43_ACTIVE_WALLET_LABEL="$label"
export S43_ACTIVE_WALLET_ROLE="$role"
export S43_ACTIVE_TOKEN_EXPIRES_AT="$expires_at"
export S43_ACTIVE_TOKEN_WARN_DAYS="$warn_days"
export ARZPLUS_TOKEN="$token"
RUNTIME

  chmod 600 "$runtime_env"

  echo "S43_ACTIVE_WALLET=$wallet_id"
  echo "RUNTIME_ENV=$runtime_env"
  echo "NEXT=source \"$runtime_env\""
}

case "${1:-check}" in
  check)
    cmd_check
    ;;
  use)
    shift
    cmd_use "${1:-}"
    ;;
  *)
    echo "USAGE: $0 {check|use <wallet_id>}"
    exit 1
    ;;
esac
