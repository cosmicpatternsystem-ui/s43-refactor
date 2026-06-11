from pathlib import Path
import re
import shutil
import time
import py_compile
import sys

TARGET = Path("s43.py")
if not TARGET.exists():
    print("ERROR: s43.py not found in current directory")
    sys.exit(1)

src = TARGET.read_text(encoding="utf-8")

# Idempotency markers
BAL_MARK = "# SAFETY_BALANCE_GUARD"
MKT_MARK = "# SAFETY_MARKET_GUARD"

if BAL_MARK in src or MKT_MARK in src:
    print("INFO: guard markers already present; no changes applied")
    sys.exit(0)

original = src

# ---------------------------------------------------------
# Patch 1: balance guard
# Anchor: line containing 'bal = await get_bal()'
# Inject immediately after that line, preserving indentation.
# ---------------------------------------------------------
balance_pat = re.compile(
    r'(?P<indent>[ \t]*)bal\s*=\s*await\s+get_bal\(\)\n'
)

def balance_repl(m):
    indent = m.group("indent")
    return (
        f'{indent}bal = await get_bal()\n'
        f'{indent}{BAL_MARK}\n'
        f'{indent}if not isinstance(bal, (int, float)):\n'
        f'{indent}    try:\n'
        f'{indent}        bal = float(bal)\n'
        f'{indent}    except Exception:\n'
        f'{indent}        bal = 0.0\n'
        f'{indent}if bal < 0:\n'
        f'{indent}    bal = 0.0\n'
    )

src, bal_n = balance_pat.subn(balance_repl, src, count=1)

# ---------------------------------------------------------
# Patch 2: market guard
# Anchor: line containing 'data = await asyncio.wait_for(fn(),'
# Inject immediately after the full assignment line.
# ---------------------------------------------------------
market_pat = re.compile(
    r'(?P<line>(?P<indent>[ \t]*)data\s*=\s*await\s+asyncio\.wait_for\(fn\(\),[^\n]*\)\n)'
)

def market_repl(m):
    indent = m.group("indent")
    line = m.group("line")
    return (
        line +
        f'{indent}{MKT_MARK}\n'
        f'{indent}if not isinstance(data, dict):\n'
        f'{indent}    data = {{}}\n'
        f'{indent}else:\n'
        f'{indent}    _tickers = data.get("tickers")\n'
        f'{indent}    if _tickers is None:\n'
        f'{indent}        _tickers = data.get("data")\n'
        f'{indent}    if isinstance(_tickers, dict) and not _tickers:\n'
        f'{indent}        data = {{}}\n'
        f'{indent}    elif isinstance(_tickers, (list, tuple, set)) and len(_tickers) == 0:\n'
        f'{indent}        data = {{}}\n'
    )

src, mkt_n = market_pat.subn(market_repl, src, count=1)

# ---------------------------------------------------------
# Validate match success
# ---------------------------------------------------------
if bal_n != 1:
    print(f"ERROR: balance anchor match count = {bal_n}, expected 1")
    sys.exit(2)

if mkt_n != 1:
    print(f"ERROR: market anchor match count = {mkt_n}, expected 1")
    sys.exit(3)

# Backup
backup = TARGET.with_name(f"s43.py.bak_guard_autopatch_{int(time.time())}")
shutil.copy2(TARGET, backup)

# Write patched file
TARGET.write_text(src, encoding="utf-8")

# Compile check
try:
    py_compile.compile(str(TARGET), doraise=True)
except Exception as e:
    print(f"ERROR: compile failed after patch: {e}")
    # rollback
    shutil.copy2(backup, TARGET)
    print(f"ROLLED BACK from backup: {backup}")
    sys.exit(4)

print("OK: patch applied successfully")
print(f"Backup: {backup}")
print("Inserted markers:")
print(f" - {BAL_MARK}")
print(f" - {MKT_MARK}")
