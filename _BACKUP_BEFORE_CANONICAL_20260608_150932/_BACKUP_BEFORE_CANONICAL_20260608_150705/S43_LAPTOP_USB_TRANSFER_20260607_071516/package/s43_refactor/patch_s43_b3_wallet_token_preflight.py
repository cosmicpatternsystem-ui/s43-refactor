#!/usr/bin/env python3
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

ROOT = os.getcwd()
RUNNER = os.path.join(ROOT, "s43_run_wallet.sh")

MARKER_BEGIN = "# S43 PATCH B3 WALLET TOKEN PREFLIGHT BEGIN"
MARKER_END = "# S43 PATCH B3 WALLET TOKEN PREFLIGHT END"

PATCH_BLOCK = r'''
# S43 PATCH B3 WALLET TOKEN PREFLIGHT BEGIN
s43_wallet_token_preflight() {
  # Best-effort wallet token preflight.
  # It only logs health status. It does NOT disable wallets and does NOT change runtime behavior.

  local _s43_root="${ROOT_DIR:-$(pwd)}"
  local _s43_log_dir="${_s43_root}/logs"
  local _s43_log_file="${_s43_log_dir}/trading_bot.log"

  mkdir -p "$_s43_log_dir" 2>/dev/null || true

  python3 - "$_s43_log_file" <<'S43_B3_PY' 2>/dev/null || true
import os
import sys
from datetime import datetime, timezone

log_file = sys.argv[1] if len(sys.argv) > 1 else None

def now_utc():
    return datetime.now(timezone.utc)

def parse_ts(value):
    if not value:
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        # Support UNIX timestamp.
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except Exception:
        pass
    try:
        # Support ISO format with Z suffix.
        v = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def emit(line):
    try:
        print(line)
    except Exception:
        pass
    if log_file:
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

now = now_utc()
total = 0
ok = 0
warning = 0
expired = 0
missing = 0
disabled = 0

for slot in (1, 2, 3):
    total += 1
    wallet = f"W{slot}"
    reg_raw = os.environ.get(f"S43_WALLET_{slot}_REGISTERED_AT", "")
    exp_raw = os.environ.get(f"S43_WALLET_{slot}_EXPIRES_AT", "")
    warn_raw = os.environ.get(f"S43_WALLET_{slot}_WARN_DAYS", "3")

    try:
        warn_days = float(warn_raw)
    except Exception:
        warn_days = 3.0

    reg_dt = parse_ts(reg_raw)
    exp_dt = parse_ts(exp_raw)

    reason = ""
    is_disabled = False

    if exp_dt is None:
        status = "MISSING"
        days_left = None
        missing += 1
        reason = "TOKEN_EXPIRY_MISSING_OR_INVALID"
    else:
        days_left = (exp_dt - now).total_seconds() / 86400.0
        if days_left < 0:
            status = "EXPIRED"
            expired += 1
            disabled += 1
            is_disabled = True
            reason = "TOKEN_EXPIRED"
        elif days_left <= warn_days:
            status = "WARNING"
            warning += 1
        else:
            status = "OK"
            ok += 1

    days_text = "nan" if days_left is None else f"{days_left:.2f}"
    reg_text = reg_dt.isoformat() if reg_dt else ""
    exp_text = exp_dt.isoformat() if exp_dt else ""

    emit(
        "event=WALLET_TOKEN_PREFLIGHT_WALLET "
        f"wallet={wallet} slot={slot} status={status} "
        f"registered_ts={reg_text} expiry_ts={exp_text} "
        f"warn_days={warn_days} days_left={days_text} "
        f"disabled={is_disabled} reason={reason}"
    )

if expired > 0:
    summary_status = "DEGRADED"
elif warning > 0 or missing > 0:
    summary_status = "WARN"
else:
    summary_status = "PASS"

emit(
    "event=WALLET_TOKEN_PREFLIGHT_SUMMARY "
    f"status={summary_status} total={total} ok={ok} "
    f"warning={warning} expired={expired} missing={missing} disabled={disabled}"
)
S43_B3_PY
}

s43_wallet_token_preflight
# S43 PATCH B3 WALLET TOKEN PREFLIGHT END
'''.strip() + "\n"


def fail(msg):
    print(f"[B3][FAIL] {msg}", file=sys.stderr)
    sys.exit(1)


def info(msg):
    print(f"[B3] {msg}")


def main():
    if not os.path.exists(RUNNER):
        fail(f"runner not found: {RUNNER}")

    with open(RUNNER, "r", encoding="utf-8", errors="replace") as f:
        src = f.read()

    if MARKER_BEGIN in src:
        info("B3 marker already exists in s43_run_wallet.sh; no changes made.")
        return

    # Prefer insertion immediately before the actual python exec line.
    patterns = [
        r'(?m)^[ \t]*exec[ \t]+python3[ \t]+"?\$DEFAULT_APP"?',
        r'(?m)^[ \t]*python3[ \t]+"?\$DEFAULT_APP"?',
        r'(?m)^[ \t]*exec[ \t]+python[ \t]+"?\$DEFAULT_APP"?',
        r'(?m)^[ \t]*python[ \t]+"?\$DEFAULT_APP"?',
    ]

    match = None
    for pat in patterns:
        m = re.search(pat, src)
        if m:
            match = m
            break

    if not match:
        fail("could not find python runner line like: exec python3 \"$DEFAULT_APP\"")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = f"{RUNNER}.bak.B3_wallet_token_preflight.{ts}"
    shutil.copy2(RUNNER, backup)
    info(f"backup created: {backup}")

    insert_at = match.start()
    new_src = src[:insert_at] + PATCH_BLOCK + "\n" + src[insert_at:]

    tmp = RUNNER + ".tmp.B3"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(new_src)

    # Preserve executable permissions.
    st = os.stat(RUNNER)
    os.chmod(tmp, st.st_mode)

    # Bash syntax check.
    chk = subprocess.run(["bash", "-n", tmp], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if chk.returncode != 0:
        os.remove(tmp)
        fail("bash syntax check failed:\n" + chk.stderr)

    os.replace(tmp, RUNNER)
    info("B3 preflight patch installed into s43_run_wallet.sh")
    info("syntax check: PASS")
    info("done")


if __name__ == "__main__":
    main()
