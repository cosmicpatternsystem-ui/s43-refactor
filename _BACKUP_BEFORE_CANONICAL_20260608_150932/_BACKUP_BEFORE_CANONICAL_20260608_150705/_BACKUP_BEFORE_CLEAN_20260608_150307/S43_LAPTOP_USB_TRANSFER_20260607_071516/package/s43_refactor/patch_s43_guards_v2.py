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

BAL_MARK = "# SAFETY_BALANCE_GUARD"
MKT_MARK = "# SAFETY_MARKET_GUARD"

if BAL_MARK in src or MKT_MARK in src:
    print("INFO: guard markers already present; no changes applied")
    sys.exit(0)

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def backup_file(path: Path):
    backup = path.with_name(f"{path.name}.bak_guard_autopatch_{int(time.time())}")
    shutil.copy2(path, backup)
    return backup

def compile_or_rollback(path: Path, backup: Path):
    try:
        py_compile.compile(str(path), doraise=True)
        return True, None
    except Exception as e:
        shutil.copy2(backup, path)
        return False, e

# --------------------------------------------------
# Patch balance: tolerant matching
# Strategy:
#   find a line assigning from await <something_bal_like>()
#   e.g. bal = await get_bal()
#        bal = await fn()
#        balance = await get_balance()
# --------------------------------------------------
balance_patterns = [
    re.compile(r'(?P<indent>[ \t]*)(?P<var>bal|balance)\s*=\s*await\s+get_bal\(\)\s*\n'),
    re.compile(r'(?P<indent>[ \t]*)(?P<var>bal|balance)\s*=\s*await\s+get_balance\(\)\s*\n'),
    re.compile(r'(?P<indent>[ \t]*)(?P<var>bal|balance)\s*=\s*await\s+[A-Za-z_][A-Za-z0-9_]*\(\)\s*\n'),
]

def inject_balance(text: str):
    for pat in balance_patterns:
        m = pat.search(text)
        if not m:
            continue
        indent = m.group("indent")
        var = m.group("var")
        start, end = m.span()
        line = text[start:end]
        injected = (
            line +
            f'{indent}{BAL_MARK}\n'
            f'{indent}if not isinstance({var}, (int, float)):\n'
            f'{indent}    try:\n'
            f'{indent}        {var} = float({var})\n'
            f'{indent}    except Exception:\n'
            f'{indent}        {var} = 0.0\n'
            f'{indent}if {var} < 0:\n'
            f'{indent}    {var} = 0.0\n'
        )
        return text[:start] + injected + text[end:], True, pat.pattern
    return text, False, None

# --------------------------------------------------
# Patch market: tolerant matching
# Strategy:
#   find a line assigning data from await asyncio.wait_for(...)
#   or direct await fn()
# --------------------------------------------------
market_patterns = [
    re.compile(r'(?P<indent>[ \t]*)(?P<var>data|snapshot|snap)\s*=\s*await\s+asyncio\.wait_for\([^\n]*\)\s*\n'),
    re.compile(r'(?P<indent>[ \t]*)(?P<var>data|snapshot|snap)\s*=\s*await\s+[A-Za-z_][A-Za-z0-9_]*\(\)\s*\n'),
]

def inject_market(text: str):
    for pat in market_patterns:
        m = pat.search(text)
        if not m:
            continue
        indent = m.group("indent")
        var = m.group("var")
        start, end = m.span()
        line = text[start:end]
        injected = (
            line +
            f'{indent}{MKT_MARK}\n'
            f'{indent}if not isinstance({var}, dict):\n'
            f'{indent}    {var} = {{}}\n'
            f'{indent}else:\n'
            f'{indent}    _tickers = {var}.get("tickers")\n'
            f'{indent}    if _tickers is None:\n'
            f'{indent}        _tickers = {var}.get("data")\n'
            f'{indent}    if isinstance(_tickers, dict) and not _tickers:\n'
            f'{indent}        {var} = {{}}\n'
            f'{indent}    elif isinstance(_tickers, (list, tuple, set)) and len(_tickers) == 0:\n'
            f'{indent}        {var} = {{}}\n'
        )
        return text[:start] + injected + text[end:], True, pat.pattern
    return text, False, None

new_src, bal_ok, bal_pat = inject_balance(src)
new_src2, mkt_ok, mkt_pat = inject_market(new_src)

if not bal_ok:
    print("ERROR: could not find tolerant balance anchor")
    sys.exit(2)

if not mkt_ok:
    print("ERROR: could not find tolerant market anchor")
    sys.exit(3)

backup = backup_file(TARGET)
TARGET.write_text(new_src2, encoding="utf-8")

ok, err = compile_or_rollback(TARGET, backup)
if not ok:
    print(f"ERROR: compile failed after patch: {err}")
    print(f"ROLLED BACK from backup: {backup}")
    sys.exit(4)

print("OK: patch applied successfully")
print(f"Backup: {backup}")
print(f"Balance pattern used: {bal_pat}")
print(f"Market pattern used:  {mkt_pat}")
print("Inserted markers:")
print(f" - {BAL_MARK}")
print(f" - {MKT_MARK}")
