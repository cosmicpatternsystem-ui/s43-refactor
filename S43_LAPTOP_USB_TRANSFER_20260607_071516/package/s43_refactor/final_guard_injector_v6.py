import sys
from pathlib import Path
import py_compile

TARGET = Path("s43.py")
lines = TARGET.read_text(encoding="utf-8").splitlines()

new_lines = []
applied_bal = False
applied_mkt = False

for line in lines:
    # 1. Balance Guard Injection (BEFORE the call to avoid breaking try/except)
    if 'bal = await self.client.get_balance()' in line and not applied_bal:
        indent = line[:line.find('bal =')]
        new_lines.append(f"{indent}# PRE-CALL SAFETY INITIALIZATION")
        new_lines.append(f"{indent}bal = 0.0") 
        new_lines.append(line) # The actual call
        new_lines.append(f"{indent}# POST-CALL GUARD")
        new_lines.append(f"{indent}if bal is None: bal = 0.0")
        new_lines.append(f"{indent}elif not isinstance(bal, (int, float, dict, list)):")
        new_lines.append(f"{indent}    try: bal = float(bal)")
        new_lines.append(f"{indent}    except: bal = 0.0")
        applied_bal = True
        continue

    # 2. Market Guard Injection
    if 'stats_map = await' in line and 'get_market_snapshot()' in line and not applied_mkt:
        indent = line[:line.find('stats_map =')]
        new_lines.append(line)
        new_lines.append(f"{indent}# SAFETY_MARKET_GUARD")
        new_lines.append(f"{indent}if not isinstance(stats_map, dict) or not stats_map:")
        new_lines.append(f"{indent}    stats_map = {{}}")
        applied_mkt = True
        continue

    new_lines.append(line)

if not applied_bal:
    print("FAILED: Could not find Balance anchor.")
    sys.exit(1)

TARGET.write_text("\n".join(new_lines), encoding="utf-8")

try:
    py_compile.compile("s43.py", doraise=True)
    print("SUCCESS: Guards applied safely BEFORE/AFTER calls. Syntax OK.")
except Exception as e:
    print(f"SYNTAX ERROR AT LINE {getattr(e, 'lineno', 'unknown')}: {e}")
    # Show context if it fails
    if hasattr(e, 'lineno'):
        start = max(0, e.lineno - 5)
        end = min(len(new_lines), e.lineno + 5)
        print("\n--- Error Context ---")
        for i in range(start, end):
            print(f"{i+1}: {new_lines[i]}")
