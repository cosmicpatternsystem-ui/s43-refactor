from pathlib import Path
import py_compile
import shutil
import time
import re

TARGET = Path("s43.py")
bak = TARGET.with_name(f"s43.py.bak_market_guard_v8_{int(time.time())}")
shutil.copy2(TARGET, bak)

text = TARGET.read_text(encoding="utf-8")
lines = text.splitlines()

if "SAFETY_MARKET_GUARD_V8" in text:
    print("[SKIP] SAFETY_MARKET_GUARD_V8 already exists")
    raise SystemExit(0)

out = []
applied = False

for line in lines:
    if (not applied) and "self._update_history(by_symbol)" in line:
        indent = line[:len(line) - len(line.lstrip(" "))]

        out.append(f"{indent}# SAFETY_MARKET_GUARD_V8")
        out.append(f"{indent}min_market_symbols = int(os.getenv('S43_MIN_MARKET_SYMBOLS', '5') or 5)")
        out.append(f"{indent}if not isinstance(by_symbol, dict) or len(by_symbol) < min_market_symbols:")
        out.append(f"{indent}    raise TradingHalt(f'MARKET_SNAPSHOT_TOO_SMALL: symbols={{len(by_symbol) if isinstance(by_symbol, dict) else 0}} min={{min_market_symbols}}')")

        applied = True

    out.append(line)

if not applied:
    print("[FAIL] could not find anchor: self._update_history(by_symbol)")
    raise SystemExit(1)

TARGET.write_text("\n".join(out) + "\n", encoding="utf-8")

print(f"[OK] backup: {bak}")
print("[OK] market guard injected")

try:
    py_compile.compile(str(TARGET), doraise=True)
    print("[OK] syntax OK after market guard injection")
except py_compile.PyCompileError as e:
    print("[FAIL] syntax error after market guard injection")
    print(e)

    m = re.search(r'line (\d+)', str(e))
    if m:
        n = int(m.group(1))
        start = max(1, n - 10)
        end = min(len(out), n + 10)
        print("\n--- context ---")
        for idx in range(start, end + 1):
            print(f"{idx}: {out[idx-1]}")

    shutil.copy2(bak, TARGET)
    print("[ROLLBACK] restored backup")
    raise SystemExit(2)
