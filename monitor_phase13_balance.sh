#!/usr/bin/env bash
set -euo pipefail

LOG="${1:-}"

if [ -z "$LOG" ]; then
  echo "usage: $0 /path/to/runtime.log"
  exit 1
fi

grep -E \
'BALANCE_REFRESH_DEGRADED|BALANCE_REFRESH_HTTP_FAIL|BALANCE_REFRESH_API_FAIL|BALANCE_REFRESH_TRANSIENT|BALANCE_REFRESH_FAIL|BALANCE_AUTH_FAIL|SAFE_CLEARED|TradingHalt|BALANCE_FETCH_FAILED' \
"$LOG" || true
