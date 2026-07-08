#!/data/data/com.termux/files/usr/bin/bash

cd "$(dirname "$0")" || exit 1

LOG_FILE="./arzplus_healthcheck.log"

echo "Running ArzPlus token healthcheck..."

if [ ! -f "test_arzplus_tokens_strict.py" ]; then
  echo "FAIL: test_arzplus_tokens_strict.py not found"
  exit 1
fi

python test_arzplus_tokens_strict.py >"$LOG_FILE" 2>&1
STATUS=$?

if [ "$STATUS" -eq 0 ]; then
  echo "PASS: ArzPlus token layout is healthy"
  echo "  slot 1 -> SET"
  echo "  slot 2 -> EMPTY"
  echo "  slot 3 -> SET"
  exit 0
else
  echo "FAIL: ArzPlus token layout has problems"
  echo ""
  echo "Details:"
  cat "$LOG_FILE"
  exit 1
fi
