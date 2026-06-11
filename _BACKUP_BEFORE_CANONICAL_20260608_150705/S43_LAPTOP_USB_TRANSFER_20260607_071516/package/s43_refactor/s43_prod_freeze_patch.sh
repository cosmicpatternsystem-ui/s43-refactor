#!/data/data/com.termux/files/usr/bin/bash
set -u

echo "============================================================"
echo "[S43-PROD-PATCH] Production freeze / verify patch started"
echo "============================================================"

ROOT="${HOME}/s43_refactor"
RUNNER="${ROOT}/s43_run_wallet.sh"
LOG="${ROOT}/logs/trading_bot.log"
ENV_FILE="${HOME}/.s43_wallet_token_metadata.env"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${ROOT}/backups/prod_freeze_${STAMP}"

cd "$ROOT" || {
  echo "[S43-PROD-PATCH] ERROR: cannot cd to $ROOT"
  exit 1
}

mkdir -p "$BACKUP_DIR" logs || {
  echo "[S43-PROD-PATCH] ERROR: cannot create backup/log directories"
  exit 1
}

echo
echo "=== Step 1/8: basic file checks ==="

if [ ! -f "$RUNNER" ]; then
  echo "[S43-PROD-PATCH] ERROR: runner not found: $RUNNER"
  exit 1
fi

echo "[S43-PROD-PATCH] runner found: $RUNNER"

if [ -f "$ENV_FILE" ]; then
  echo "[S43-PROD-PATCH] persistent env found: $ENV_FILE"
else
  echo "[S43-PROD-PATCH] WARNING: persistent env not found: $ENV_FILE"
fi

echo
echo "=== Step 2/8: backups ==="

cp -a "$RUNNER" "${BACKUP_DIR}/s43_run_wallet.sh.${STAMP}.bak" || {
  echo "[S43-PROD-PATCH] ERROR: runner backup failed"
  exit 1
}

if [ -f "$ENV_FILE" ]; then
  cp -a "$ENV_FILE" "${BACKUP_DIR}/s43_wallet_token_metadata.env.${STAMP}.bak" || {
    echo "[S43-PROD-PATCH] ERROR: env backup failed"
    exit 1
  }
fi

echo "[S43-PROD-PATCH] backup dir: $BACKUP_DIR"

echo
echo "=== Step 3/8: idempotent B3 literal repair + compile validation ==="

python - <<'INNERPY'
from pathlib import Path
from datetime import datetime
import re
import sys

runner = Path("s43_run_wallet.sh")
text = runner.read_text(encoding="utf-8")
original = text

replacements = [
    (
        r'"event=\s+WALLET_TOKEN_PREFLIGHT_WALLET\s+"',
        '"event=WALLET_TOKEN_PREFLIGHT_WALLET "',
        "WALLET_TOKEN_PREFLIGHT_WALLET",
    ),
    (
        r'"event=\s+WALLET_TOKEN_PREFLIGHT_SUMMARY\s+"',
        '"event=WALLET_TOKEN_PREFLIGHT_SUMMARY "',
        "WALLET_TOKEN_PREFLIGHT_SUMMARY",
    ),
]

changed = False
for pattern, repl, label in replacements:
    new_text = re.sub(pattern, repl, text, flags=re.S)
    if new_text != text:
        print(f"[S43-PROD-PATCH] repaired literal: {label}")
        changed = True
        text = new_text

if changed:
    backup = runner.with_name(
        runner.name + f".bak.prod_freeze_literal_fix.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    backup.write_text(original, encoding="utf-8")
    runner.write_text(text, encoding="utf-8")
    print(f"[S43-PROD-PATCH] local pre-repair backup: {backup}")
else:
    print("[S43-PROD-PATCH] B3 event literals already clean")

text2 = runner.read_text(encoding="utf-8")
m = re.search(r"<<'S43_B3_PY'.*?\n(.*?)\nS43_B3_PY", text2, flags=re.S)
if not m:
    print("[S43-PROD-PATCH] ERROR: S43_B3_PY heredoc not found")
    sys.exit(1)

code = m.group(1)
try:
    compile(code, "S43_B3_PY", "exec")
except SyntaxError as e:
    print("[S43-PROD-PATCH] ERROR: B3 embedded Python compile failed")
    print(f"  {e.__class__.__name__}: {e}")
    print(f"  line={e.lineno} offset={e.offset} text={e.text!r}")
    sys.exit(1)

print("[S43-PROD-PATCH] B3 embedded Python compile: PASS")
INNERPY

if [ $? -ne 0 ]; then
  echo "[S43-PROD-PATCH] ERROR: B3 repair/compile step failed"
  exit 1
fi

echo
echo "=== Step 4/8: shell syntax validation ==="

if bash -n "$RUNNER"; then
  echo "[S43-PROD-PATCH] shell syntax: PASS"
else
  echo "[S43-PROD-PATCH] ERROR: shell syntax failed"
  exit 1
fi

echo
echo "=== Step 5/8: marker and order validation ==="

B4_LINE="$(grep -n 'B4 WALLET TOKEN ENV GUARD BEGIN\|S43 PATCH B4\|WALLET_TOKEN_ENV_GUARD' "$RUNNER" | head -n1 | cut -d: -f1 || true)"
B3_LINE="$(grep -n '# S43 PATCH B3 WALLET TOKEN PREFLIGHT BEGIN' "$RUNNER" | head -n1 | cut -d: -f1 || true)"
B2_MARKER_LINE="$(grep -n 'WALLET_TOKEN_METADATA' "$RUNNER" | head -n1 | cut -d: -f1 || true)"

echo "[S43-PROD-PATCH] B4 first marker line: ${B4_LINE:-not-found}"
echo "[S43-PROD-PATCH] B3 marker line: ${B3_LINE:-not-found}"
echo "[S43-PROD-PATCH] B2 metadata marker line in runner if present: ${B2_MARKER_LINE:-not-found}"

if [ -z "$B4_LINE" ]; then
  echo "[S43-PROD-PATCH] ERROR: B4 marker/event not found in runner"
  exit 1
fi

if [ -z "$B3_LINE" ]; then
  echo "[S43-PROD-PATCH] ERROR: B3 marker not found in runner"
  exit 1
fi

if [ "$B4_LINE" -lt "$B3_LINE" ]; then
  echo "[S43-PROD-PATCH] static order B4 before B3: PASS"
else
  echo "[S43-PROD-PATCH] ERROR: B4 does not appear before B3"
  exit 1
fi

if grep -q 's43_wallet_token_preflight' "$RUNNER"; then
  echo "[S43-PROD-PATCH] B3 function/call marker exists: PASS"
else
  echo "[S43-PROD-PATCH] ERROR: B3 function/call marker missing"
  exit 1
fi

echo
echo "=== Step 6/8: persistent env validation, TOKEN redacted ==="

if [ -f "$ENV_FILE" ]; then
  echo "--- persisted wallet metadata keys ---"
  grep -E '^(export[[:space:]]+)?S43_WALLET_[123]_' "$ENV_FILE" | sed -E 's/(TOKEN=).*/\1***REDACTED***/' || true

  for i in 1 2 3; do
    if grep -Eq "^(export[[:space:]]+)?S43_WALLET_${i}_REGISTERED_AT=" "$ENV_FILE" &&
       grep -Eq "^(export[[:space:]]+)?S43_WALLET_${i}_EXPIRES_AT=" "$ENV_FILE" &&
       grep -Eq "^(export[[:space:]]+)?S43_WALLET_${i}_WARN_DAYS=" "$ENV_FILE"; then
      echo "[S43-PROD-PATCH] env wallet W${i}: PASS"
    else
      echo "[S43-PROD-PATCH] WARNING: env wallet W${i}: incomplete metadata"
    fi
  done
else
  echo "[S43-PROD-PATCH] WARNING: env file missing; runtime may still work if env already exported"
fi

echo
echo "=== Step 7/8: runtime smoke test B4 -> B3 -> B2 ==="

BEFORE="$(wc -l < "$LOG" 2>/dev/null || echo 0)"

echo "[S43-PROD-PATCH] running: ./s43_run_wallet.sh 1"
echo "[S43-PROD-PATCH] output file: ${ROOT}/.s43_prod_freeze_smoke_${STAMP}.out"

./s43_run_wallet.sh 1 > "${ROOT}/.s43_prod_freeze_smoke_${STAMP}.out" 2>&1
RUN_RC=$?

echo "[S43-PROD-PATCH] runner exit code: $RUN_RC"

NEW_EVENTS="$(tail -n +"$((BEFORE+1))" "$LOG" 2>/dev/null | grep -E 'WALLET_TOKEN_ENV_GUARD|WALLET_TOKEN_PREFLIGHT|WALLET_TOKEN_METADATA' || true)"

echo "--- new wallet token events ---"
printf '%s\n' "$NEW_EVENTS"

if printf '%s\n' "$NEW_EVENTS" | grep -q 'WALLET_TOKEN_ENV_GUARD_SUMMARY.*status=PASS'; then
  echo "[S43-PROD-PATCH] B4 runtime summary: PASS"
else
  echo "[S43-PROD-PATCH] ERROR: B4 runtime PASS summary not found"
  exit 1
fi

if printf '%s\n' "$NEW_EVENTS" | grep -q 'WALLET_TOKEN_PREFLIGHT_SUMMARY.*status=PASS'; then
  echo "[S43-PROD-PATCH] B3 runtime summary: PASS"
else
  echo "[S43-PROD-PATCH] ERROR: B3 runtime PASS summary not found"
  exit 1
fi

if printf '%s\n' "$NEW_EVENTS" | grep -q 'WALLET_TOKEN_METADATA.*status=OK'; then
  echo "[S43-PROD-PATCH] B2 runtime metadata: PASS"
else
  echo "[S43-PROD-PATCH] ERROR: B2 runtime metadata OK not found"
  exit 1
fi

TMP_EVENTS="${ROOT}/.s43_prod_freeze_events_${STAMP}.txt"
printf '%s\n' "$NEW_EVENTS" > "$TMP_EVENTS"

L_B4="$(grep -n 'WALLET_TOKEN_ENV_GUARD_SUMMARY' "$TMP_EVENTS" | head -n1 | cut -d: -f1 || true)"
L_B3="$(grep -n 'WALLET_TOKEN_PREFLIGHT_SUMMARY' "$TMP_EVENTS" | head -n1 | cut -d: -f1 || true)"
L_B2="$(grep -n 'WALLET_TOKEN_METADATA' "$TMP_EVENTS" | head -n1 | cut -d: -f1 || true)"

echo "[S43-PROD-PATCH] runtime order lines: B4=${L_B4:-NA}, B3=${L_B3:-NA}, B2=${L_B2:-NA}"

if [ -n "$L_B4" ] && [ -n "$L_B3" ] && [ -n "$L_B2" ] && [ "$L_B4" -lt "$L_B3" ] && [ "$L_B3" -lt "$L_B2" ]; then
  echo "[S43-PROD-PATCH] runtime order B4 -> B3 -> B2: PASS"
else
  echo "[S43-PROD-PATCH] ERROR: runtime order B4 -> B3 -> B2 not confirmed"
  exit 1
fi

echo
echo "=== Step 8/8: production snapshot ==="

SNAPSHOT="${ROOT}/s43_prod_freeze_${STAMP}.tar.gz"
MANIFEST="${ROOT}/s43_prod_freeze_${STAMP}.manifest.txt"

{
  echo "S43 production freeze manifest"
  echo "timestamp=${STAMP}"
  echo "root=${ROOT}"
  echo
  echo "runner_sha256:"
  sha256sum "$RUNNER" 2>/dev/null || true
  echo
  echo "env_sha256:"
  if [ -f "$ENV_FILE" ]; then
    sha256sum "$ENV_FILE" 2>/dev/null || true
  else
    echo "env_file_missing"
  fi
  echo
  echo "final_status:"
  echo "B4_ENV_GUARD=PASS"
  echo "B3_PREFLIGHT=PASS"
  echo "B2_RUNTIME_METADATA=PASS"
  echo "ORDER_B4_B3_B2=PASS"
} > "$MANIFEST"

tar -czf "$SNAPSHOT" s43_run_wallet.sh logs/trading_bot.log "$(basename "$MANIFEST")" 2>/dev/null || true

if [ -f "$SNAPSHOT" ]; then
  sha256sum "$SNAPSHOT" > "${SNAPSHOT}.sha256" 2>/dev/null || true
  echo "[S43-PROD-PATCH] snapshot: $SNAPSHOT"
  echo "[S43-PROD-PATCH] snapshot sha256: ${SNAPSHOT}.sha256"
else
  echo "[S43-PROD-PATCH] WARNING: snapshot tar creation failed"
fi

echo
echo "============================================================"
echo "[S43-PROD-PATCH] FINAL STATUS: PRODUCTION READY"
echo "B4 -> B3 -> B2: PASS"
echo "Backups: $BACKUP_DIR"
echo "Manifest: $MANIFEST"
echo "============================================================"
