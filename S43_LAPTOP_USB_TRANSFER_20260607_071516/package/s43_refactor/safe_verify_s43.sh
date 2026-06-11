#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

PROJECT_DIR="$HOME/s43_refactor"
TARGET="$PROJECT_DIR/s43.py"
TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="$PROJECT_DIR/s43_clean_compile_ok_${TS}.py"
LOGFILE="$PROJECT_DIR/retry_after_exchange_fix_${TS}.log"

echo "[1/6] Enter project dir"
cd "$PROJECT_DIR"

echo "[2/6] Check target file"
if [ ! -f "$TARGET" ]; then
  echo "ERROR: s43.py not found at: $TARGET"
  exit 1
fi

echo "[3/6] Create safe backup"
cp -f "$TARGET" "$BACKUP"
echo "BACKUP_OK: $BACKUP"

echo "[4/6] Compile check"
python -m py_compile "$TARGET"
echo "COMPILE_OK"

echo "[5/6] Run safe status check"
python "$TARGET" 2>&1 | tee "$LOGFILE"

echo "[6/6] Extract key lines"
grep -n "403\|توکن نامعتبر\|balance_ok\|balance_failed\|summary\|ISOCHK_GLOBAL" "$LOGFILE" || true

echo "DONE"
echo "LOGFILE=$LOGFILE"
