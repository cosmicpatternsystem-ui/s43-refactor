import sys
from pathlib import Path
import py_compile

TARGET = Path("s43.py")
lines = TARGET.read_text(encoding="utf-8").splitlines()

new_lines = []
applied_bal = False
applied_mkt = False

for line in lines:
    new_lines.append(line)
    
    # 1. Balance Guard Injection (with exact indentation)
    if 'bal = await self.client.get_balance()' in line and not applied_bal:
        indent = line[:line.find('bal =')]
        new_lines.append(f"{indent}# SAFETY_BALANCE_GUARD")
        new_lines.append(f"{indent}if bal is None: bal = 0.0")
        new_lines.append(f"{indent}elif not isinstance(bal, (int, float, dict, list)):")
        new_lines.append(f"{indent}    try: bal = float(bal)")
        new_lines.append(f"{indent}    except: bal = 0.0")
        applied_bal = True

    # 2. Market Guard Injection
    if 'stats_map = await' in line and 'get_market_snapshot()' in line and not applied_mkt:
        indent = line[:line.find('stats_map =')]
        new_lines.append(f"{indent}# SAFETY_MARKET_GUARD")
        new_lines.append(f"{indent}if not isinstance(stats_map, dict) or not stats_map:")
        new_lines.append(f"{indent}    stats_map = {{}}")
        applied_mkt = True

if not applied_bal:
    print("FAILED: Could not find Balance anchor.")
    sys.exit(1)

# Write back
TARGET.write_text("\n".join(new_lines), encoding="utf-8")

# Final Compile Test
try:
    py_compile.compile("s43.py", doraise=True)
    print("SUCCESS: Guards applied. No Persian chars in guards. Syntax OK.")
except Exception as e:
    print(f"STILL PROB: {e}")
    # Show the context of the error
    import traceback
    traceback.print_exc()
