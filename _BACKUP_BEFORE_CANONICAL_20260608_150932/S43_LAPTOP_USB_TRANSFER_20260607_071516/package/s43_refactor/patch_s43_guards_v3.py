from pathlib import Path
import re
import shutil
import time
import py_compile
import sys

TARGET = Path("s43.py")
if not TARGET.exists():
    print("ERROR: s43.py not found")
    sys.exit(1)

src = TARGET.read_text(encoding="utf-8")

BAL_MARK = "# SAFETY_BALANCE_GUARD"
MKT_MARK = "# SAFETY_MARKET_GUARD"

if BAL_MARK in src or MKT_MARK in src:
    print("INFO: guard marker already present; no changes applied")
    sys.exit(0)

def backup_file(path: Path):
    b = path.with_name(f"{path.name}.bak_guard_v3_{int(time.time())}")
    shutil.copy2(path, b)
    return b

def compile_or_rollback(path: Path, backup: Path):
    try:
        py_compile.compile(str(path), doraise=True)
        return True, None
    except Exception as e:
        shutil.copy2(backup, path)
        return False, e

# ---------------------------------------------------------
# BALANCE PATCH
# Exact real anchor from your grep:
#   bal = await self.client.get_balance()
# ---------------------------------------------------------
bal_pat = re.compile(
    r'(?P<indent>[ \t]*)bal\s*=\s*await\s+self\.client\.get_balance\(\)\s*\n'
)

def bal_repl(m):
    indent = m.group("indent")
    return (
        f'{indent}bal = await self.client.get_balance()\n'
        f'{indent}{BAL_MARK}\n'
        f'{indent}if bal is None:\n'
        f'{indent}    bal = 0.0\n'
        f'{indent}elif not isinstance(bal, (int, float, dict, list, tuple)):\n'
        f'{indent}    try:\n'
        f'{indent}        bal = float(bal)\n'
        f'{indent}    except Exception:\n'
        f'{indent}        bal = 0.0\n'
    )

src2, bal_n = bal_pat.subn(bal_repl, src, count=1)

if bal_n != 1:
    print(f"ERROR: exact balance anchor not found, match count={bal_n}")
    sys.exit(2)

# ---------------------------------------------------------
# MARKET PATCH
# Real anchor from your grep:
#   stats_map = await asyncio.wait_for(self.public.get_market_snapshot(), timeout=...)
# Make pattern tolerant to spaces and long timeout expression.
# ---------------------------------------------------------
mkt_pat = re.compile(
    r'(?P<indent>[ \t]*)stats_map\s*=\s*await\s+asyncio\.wait_for\(\s*self\.public\.get_market_snapshot\(\)\s*,\s*timeout\s*=\s*[^\n]+\)\s*\n'
)

def mkt_repl(m):
    indent = m.group("indent")
    return (
        m.group(0) +
        f'{indent}{MKT_MARK}\n'
        f'{indent}if not isinstance(stats_map, dict):\n'
        f'{indent}    stats_map = {{}}\n'
        f'{indent}else:\n'
        f'{indent}    if not stats_map:\n'
        f'{indent}        stats_map = {{}}\n'
    )

src3, mkt_n = mkt_pat.subn(mkt_repl, src2, count=1)

if mkt_n != 1:
    print(f"ERROR: exact market anchor not found, match count={mkt_n}")
    sys.exit(3)

backup = backup_file(TARGET)
TARGET.write_text(src3, encoding="utf-8")

ok, err = compile_or_rollback(TARGET, backup)
if not ok:
    print(f"ERROR: compile failed after patch: {err}")
    print(f"ROLLED BACK from backup: {backup}")
    sys.exit(4)

print("OK: patch applied successfully")
print(f"Backup: {backup}")
print(f"Inserted: {BAL_MARK}")
print(f"Inserted: {MKT_MARK}")
