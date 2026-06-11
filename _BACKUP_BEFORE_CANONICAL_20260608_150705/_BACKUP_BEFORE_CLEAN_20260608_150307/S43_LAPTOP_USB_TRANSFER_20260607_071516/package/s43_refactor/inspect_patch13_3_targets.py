from pathlib import Path
import re

src = Path("s43.py").read_text(encoding="utf-8")
lines = src.splitlines()

print("=== function defs containing balance ===")
for i, line in enumerate(lines, 1):
    if re.search(r'\b(async\s+def|def)\b.*balance', line):
        print(f"{i}: {line!r}")

print("\n=== key BALANCE_FETCH_FAILED targets ===")
keys = [
    "DASH_PORTFOLIO_BALANCE",
    "BALANCE_FETCH_FAILED: TRANSIENT",
    "BALANCE_FETCH_FAILED: HTTP_FAIL",
    "BALANCE_FETCH_FAILED: API_FAIL",
    'BALANCE_FETCH_FAILED: EXC',
    "ARZPLUS_FAST_PARSE_FAIL",
    "PARSE_OK_FALSE",
]
for i, line in enumerate(lines, 1):
    if any(k in line for k in keys):
        print(f"{i}: {line!r}")

print("\n=== last_balance markers ===")
for i, line in enumerate(lines, 1):
    if any(k in line for k in ["last_balance_ok", "last_balance_err", "last_balance_ts", "cash_irt"]):
        if 13900 <= i <= 14400:
            print(f"{i}: {line!r}")
