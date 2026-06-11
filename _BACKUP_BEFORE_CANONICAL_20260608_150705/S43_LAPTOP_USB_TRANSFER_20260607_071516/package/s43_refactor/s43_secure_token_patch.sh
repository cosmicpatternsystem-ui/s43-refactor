#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

CONFIG_DIR="$ROOT_DIR/config"
REGISTRY="$CONFIG_DIR/s43_wallet_registry.env"
BACKUP_DIR="$ROOT_DIR/backups"

mkdir -p "$CONFIG_DIR" "$BACKUP_DIR"
chmod 700 "$CONFIG_DIR" "$BACKUP_DIR" 2>/dev/null || true

TODAY="$(date +%F)"
DEFAULT_LIFETIME_DAYS="${DEFAULT_TOKEN_LIFETIME_DAYS:-30}"
DEFAULT_WARN_DAYS="${DEFAULT_WARN_DAYS:-7}"

touch "$REGISTRY"
chmod 600 "$REGISTRY"

backup_registry() {
  cp "$REGISTRY" "$BACKUP_DIR/s43_wallet_registry.env.$(date +%Y%m%d_%H%M%S).bak"
}

set_kv() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" "$REGISTRY" 2>/dev/null; then
    sed -i "s|^${key}=.*|${key}=\"${value}\"|g" "$REGISTRY"
  else
    printf '%s="%s"\n' "$key" "$value" >> "$REGISTRY"
  fi
}

calc_default_expiry() {
  date -d "$TODAY + $DEFAULT_LIFETIME_DAYS days" +%F 2>/dev/null || python3 - <<PY
from datetime import datetime, timedelta
print((datetime.strptime("$TODAY","%Y-%m-%d") + timedelta(days=$DEFAULT_LIFETIME_DAYS)).strftime("%Y-%m-%d"))
PY
}

upsert_wallet_token() {
  local wallet_id="$1"
  local label="$2"

  printf 'Update wallet %s (%s)? [y/N]: ' "$wallet_id" "$label"
  read -r update_choice || true
  case "${update_choice:-N}" in
    y|Y|yes|YES) ;;
    *) return 0 ;;
  esac

  printf 'Wallet %s token: ' "$wallet_id"
  stty -echo
  read -r token || true
  stty echo
  printf '\n'

  if [ -z "${token:-}" ]; then
    echo "INFO: empty token, wallet $wallet_id skipped"
    return 0
  fi

  local expiry_input=""
  local warn_input=""
  local expiry_date=""
  local warn_days=""

  printf 'Expiry date YYYY-MM-DD [auto=%s]: ' "$(calc_default_expiry)"
  read -r expiry_input || true

  if [ -n "${expiry_input:-}" ]; then
    expiry_date="$expiry_input"
  else
    expiry_date="$(calc_default_expiry)"
  fi

  printf 'Warn days before expiry [%s]: ' "$DEFAULT_WARN_DAYS"
  read -r warn_input || true
  warn_days="${warn_input:-$DEFAULT_WARN_DAYS}"

  set_kv "ARZPLUS_WALLET_${wallet_id}_TOKEN" "$token"
  set_kv "ARZPLUS_WALLET_${wallet_id}_REGISTERED_AT" "$TODAY"
  set_kv "ARZPLUS_WALLET_${wallet_id}_EXPIRES_AT" "$expiry_date"
  set_kv "ARZPLUS_WALLET_${wallet_id}_WARN_DAYS" "$warn_days"
  set_kv "ARZPLUS_WALLET_${wallet_id}_STATUS" "active"

  echo "UPDATED wallet=$wallet_id label=$label registered_at=$TODAY expires_at=$expiry_date warn_days=$warn_days"
}

backup_registry

set_kv "ARZPLUS_WALLET_1_LABEL" "core_alpha"
set_kv "ARZPLUS_WALLET_1_ROLE" "primary_high_efficiency"

set_kv "ARZPLUS_WALLET_2_LABEL" "capital_shield"
set_kv "ARZPLUS_WALLET_2_ROLE" "capital_preservation"

set_kv "ARZPLUS_WALLET_3_LABEL" "strategic_lab"
set_kv "ARZPLUS_WALLET_3_ROLE" "team_growth_and_experiments"

upsert_wallet_token 1 "core_alpha"
upsert_wallet_token 2 "capital_shield"
upsert_wallet_token 3 "strategic_lab"

echo "S43_SECURE_TOKEN_PATCH_DONE"
