#!/usr/bin/env bash
set -u

PY="${PYTHON:-python}"
TARGET="s43.py"
STAMP="$(date +%Y%m%d_%H%M%S)"
CURRENT_BACKUP="s43.py.before_autofix_v2_${STAMP}"
TMP_OUT=".s43_pycompile_${STAMP}.out"

echo "[1/5] Checking files..."

if [ ! -f "$TARGET" ]; then
  echo "ERROR: s43.py not found in current directory."
  exit 1
fi

if ! command -v "$PY" >/dev/null 2>&1; then
  echo "ERROR: python not found. Try: pkg install python"
  exit 1
fi

echo "[2/5] Backing up current s43.py -> $CURRENT_BACKUP"
cp "$TARGET" "$CURRENT_BACKUP" || {
  echo "ERROR: backup failed."
  exit 1
}

compile_ok() {
  "$PY" -m py_compile "$1" >"$TMP_OUT" 2>&1
}

echo "[3/5] Running py_compile on current s43.py..."
if compile_ok "$TARGET"; then
  echo "OK: current s43.py already compiles."
  echo
  echo "Current references:"
  grep -n "_ws_top8_compact_panel\|top8_compact_panel(" "$TARGET" 2>/dev/null || true
  rm -f "$TMP_OUT"
  exit 0
fi

echo "Current s43.py has syntax error:"
cat "$TMP_OUT"
echo

echo "[4/5] Searching for latest valid backup..."

GOOD_BACKUP=""

for B in $(ls -t s43.py.bak_top8_compact_v3 s43.py.bak_top8_compact_v2 s43.py.bak_top8_compact s43.py.bak_top8_compact_* s43.py.bak_* 2>/dev/null | awk '!seen[$0]++'); do
  [ -f "$B" ] || continue
  echo "Testing backup: $B"
  if compile_ok "$B"; then
    GOOD_BACKUP="$B"
    break
  else
    ERR_LINE="$(head -3 "$TMP_OUT" | tr '\n' ' ')"
    echo "  not valid: $ERR_LINE"
  fi
done

if [ -z "$GOOD_BACKUP" ]; then
  echo
  echo "ERROR: no valid backup found."
  echo "Your current file is saved as: $CURRENT_BACKUP"
  echo
  echo "Now show the broken area with:"
  echo "sed -n '27140,27175p' s43.py"
  rm -f "$TMP_OUT"
  exit 1
fi

echo
echo "Valid backup found: $GOOD_BACKUP"
echo "[5/5] Restoring $GOOD_BACKUP -> s43.py"
cp "$GOOD_BACKUP" "$TARGET" || {
  echo "ERROR: restore failed."
  rm -f "$TMP_OUT"
  exit 1
}

echo "Verifying restored s43.py..."
if compile_ok "$TARGET"; then
  echo "OK: restored s43.py compiles successfully."
else
  echo "ERROR: restored file still fails py_compile:"
  cat "$TMP_OUT"
  rm -f "$TMP_OUT"
  exit 1
fi

echo
echo "Current references:"
grep -n "_ws_top8_compact_panel\|top8_compact_panel(" "$TARGET" 2>/dev/null || true

echo
echo "Done."
echo "Pre-fix copy saved as: $CURRENT_BACKUP"
echo "Restored from: $GOOD_BACKUP"

rm -f "$TMP_OUT"
