#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

TARGET="${1:-s43.py}"
OUTDIR="${2:-runtime_probes}"
TS="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTDIR"

if [ ! -f "$TARGET" ]; then
  echo "[ERR] target not found: $TARGET"
  exit 1
fi

OUTFILE="$OUTDIR/s43_hotspots_${TS}.txt"

show_block() {
  local start="$1"
  local end="$2"
  local title="$3"
  echo "===== ${title} (${start}-${end}) ====="
  sed -n "${start},${end}p" "$TARGET" || true
  echo
}

{
  echo "FILE: $TARGET"
  echo "TS: $TS"
  echo

  echo "===== SYMBOL INDEX ====="
  grep -n '^class RiskManager' "$TARGET" || true
  grep -n '^class ExecutionEngine' "$TARGET" || true
  grep -n '^class TradingBotBase' "$TARGET" || true
  grep -n '^class TradingBotOps' "$TARGET" || true
  grep -n '^class TradingBot' "$TARGET" || true
  echo

  echo "===== FUNCTION INDEX ====="
  grep -n 'def can_open_explain' "$TARGET" || true
  grep -n 'def size_notional' "$TARGET" || true
  grep -n 'def place_limit' "$TARGET" || true
  grep -n 'def _process_symbol_heartbeat' "$TARGET" || true
  grep -n 'def run(self' "$TARGET" || true
  echo

  show_block 10920 11120 "RiskManager region"
  show_block 11290 11450 "ExecutionEngine.place_limit region"
  show_block 19580 20520 "_process_symbol_heartbeat region"
  show_block 21440 21620 "TradingBotOps.run / surrounding"
  show_block 23135 23250 "TradingBot final class"
  show_block 23650 23840 "top-level run"
  show_block 29430 29445 "__main__ tail"

  echo "===== TARGETED SEARCH ====="
  grep -n 'can_open_explain(' "$TARGET" || true
  grep -n 'size_notional(' "$TARGET" || true
  grep -n 'place_order(' "$TARGET" || true
  grep -n '\.place_limit(' "$TARGET" || true
  grep -n 'api.place_limit(' "$TARGET" || true
  grep -n 'w\.exec\.place_limit(' "$TARGET" || true
  echo
} > "$OUTFILE"

echo "[OK] wrote: $OUTFILE"
echo
echo "----- HEAD(140) -----"
sed -n '1,140p' "$OUTFILE"
echo
echo "----- MID SEARCH -----"
grep -n '===== ' "$OUTFILE" || true
echo
echo "----- TAIL(140) -----"
tail -n 140 "$OUTFILE" || true
