#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

PROJECT_DIR="$HOME/s43_refactor"
TARGET="$PROJECT_DIR/s43.py"
TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="$PROJECT_DIR/s43_clean_compile_ok_${TS}.py"
LOGFILE="$PROJECT_DIR/retry_after_exchange_fix_${TS}.log"
SUMMARY="$PROJECT_DIR/s43_verify_summary_${TS}.txt"

cd "$PROJECT_DIR"

echo "========================================"
echo " S43 SAFE VERIFY V3"
echo "========================================"
echo "PROJECT_DIR=$PROJECT_DIR"
echo "TARGET=$TARGET"
echo "LOGFILE=$LOGFILE"
echo "SUMMARY=$SUMMARY"
echo "========================================"

echo "[1/7] Checking target file..."
if [ ! -f "$TARGET" ]; then
  echo "ERROR: s43.py not found at: $TARGET"
  exit 1
fi
echo "TARGET_OK"

echo "[2/7] Creating backup..."
cp -f "$TARGET" "$BACKUP"
echo "BACKUP_OK: $BACKUP"

echo "[3/7] Python compile check..."
python -m py_compile "$TARGET"
echo "COMPILE_OK"

echo "[4/7] Running safe status check..."
set +e
python "$TARGET" 2>&1 | tee "$LOGFILE"
RUN_RC=${PIPESTATUS[0]:-0}
set -e

echo "[5/7] Extracting key lines..."
echo "----------------------------------------"
grep -n "403\|توکن نامعتبر\|token_present\|auth_scheme\|balance_ok\|balance_failed\|summary\|ISOCHK_GLOBAL" "$LOGFILE" || true
echo "----------------------------------------"

echo "[6/7] Building summary..."

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
  printf '%s\n' "S43_SAFE_VERIFY_V3"
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
} | tee "$SUMMARY"

echo "[7/7] Final decision..."
echo "----------------------------------------"
cat "$SUMMARY"
echo "----------------------------------------"

if [ "$FINAL_STATUS" = "API_403_INVALID_TOKEN" ]; then
  echo "RESULT: FAIL_REMOTE_AUTH"
elif [ "$FINAL_STATUS" = "BALANCE_ALL_OK" ]; then
  echo "RESULT: PASS"
else
  echo "RESULT: CHECK_LOG"
fi

echo "DONE"
echo "LOGFILE=$LOGFILE"
echo "SUMMARY=$SUMMARY"
