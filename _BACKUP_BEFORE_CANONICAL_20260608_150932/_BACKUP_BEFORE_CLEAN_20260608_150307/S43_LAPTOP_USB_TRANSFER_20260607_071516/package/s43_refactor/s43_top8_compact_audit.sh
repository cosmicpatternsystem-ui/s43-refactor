#!/usr/bin/env bash
set -u

TARGET="s43.py"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="s43.py.before_top8_audit_${STAMP}"

if [ ! -f "$TARGET" ]; then
  echo "ERROR: s43.py not found."
  exit 1
fi

cp "$TARGET" "$BACKUP" || {
  echo "ERROR: backup failed."
  exit 1
}

echo "Backup: $BACKUP"
echo
echo "=== grep: top8_compact_panel / _ws_top8_compact_panel ==="
grep -n "_ws_top8_compact_panel\|top8_compact_panel" "$TARGET" || true

echo
TOP8_LINES="$(grep -n "top8_compact_panel" "$TARGET" | cut -d: -f1)"
COUNT_TOP8="$(grep -c "top8_compact_panel" "$TARGET" 2>/dev/null || echo 0)"
COUNT_WS="$(grep -c "_ws_top8_compact_panel" "$TARGET" 2>/dev/null || echo 0)"

echo "count(top8_compact_panel)=$COUNT_TOP8"
echo "count(_ws_top8_compact_panel)=$COUNT_WS"
echo

DEF_LINE="$(grep -n "def top8_compact_panel(symbols):" "$TARGET" | head -1 | cut -d: -f1)"

if [ -n "${DEF_LINE:-}" ]; then
  START=$((DEF_LINE-20))
  END=$((DEF_LINE+80))
  [ "$START" -lt 1 ] && START=1
  echo "=== context around def top8_compact_panel(symbols): lines ${START}-${END} ==="
  sed -n "${START},${END}p" "$TARGET"
else
  echo "Definition line not found."
fi

echo
if [ "$COUNT_TOP8" = "1" ] && [ "$COUNT_WS" = "0" ]; then
  echo "ASSESSMENT: likely dead nested function (definition only, no direct call site found)."
else
  echo "ASSESSMENT: more than one occurrence found; inspect call sites before any refactor."
fi

echo
echo "No changes were made to s43.py"
