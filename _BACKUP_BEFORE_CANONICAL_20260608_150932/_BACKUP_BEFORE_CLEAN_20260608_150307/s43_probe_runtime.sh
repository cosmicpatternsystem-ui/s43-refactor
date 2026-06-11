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

OUTFILE="$OUTDIR/s43_runtime_probe_${TS}.txt"

{
  echo "FILE: $TARGET"
  echo "TS: $TS"
  echo

  echo "===== ENTRYPOINT SEARCH ====="
  grep -n '^def run(' "$TARGET" || true
  grep -n '^def _run_raz_entry(' "$TARGET" || true
  grep -n '^if __name__ == "__main__":' "$TARGET" || true
  grep -n 'main()' "$TARGET" | head -n 20 || true
  echo

  echo "===== BOOTSTRAP SNIPPETS ====="
  sed -n '14240,14520p' "$TARGET" || true
  echo
  sed -n '23640,23860p' "$TARGET" || true
  echo

  echo "===== BOT CLASS / OPS ====="
  grep -n '^class TradingBot' "$TARGET" || true
  grep -n 'def run(self' "$TARGET" | head -n 50 || true
  echo
  sed -n '21440,21660p' "$TARGET" || true
  echo
  sed -n '23120,23260p' "$TARGET" || true
  echo

  echo "===== HEARTBEAT / DECISION PATH ====="
  grep -n '_process_symbol_heartbeat' "$TARGET" || true
  echo
  sed -n '19580,20480p' "$TARGET" || true
  echo

  echo "===== RISK GATES ====="
  grep -n 'can_open_explain' "$TARGET" || true
  grep -n 'size_notional' "$TARGET" || true
  echo
  sed -n '10920,11110p' "$TARGET" || true
  echo

  echo "===== EXECUTION PATH ====="
  grep -n 'class ExecutionEngine' "$TARGET" || true
  grep -n 'def place_limit' "$TARGET" || true
  grep -n 'place_order(' "$TARGET" | head -n 80 || true
  echo
  sed -n '11280,11460p' "$TARGET" || true
  echo

  echo "===== DIRECT EXCHANGE CALL SITES ====="
  grep -n 'exchange.*place_order' "$TARGET" || true
  grep -n 'client.*place_order' "$TARGET" || true
  grep -n '\.place_market(' "$TARGET" || true
  grep -n '\.place_limit(' "$TARGET" || true
  echo
} > "$OUTFILE"

echo "[OK] wrote: $OUTFILE"
echo
echo "----- HEAD(120) -----"
sed -n '1,120p' "$OUTFILE"
echo
echo "----- TAIL(120) -----"
tail -n 120 "$OUTFILE" || true
