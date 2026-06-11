from pathlib import Path
import py_compile
import shutil
import time
import re

TARGET = Path("s43.py")
bak = TARGET.with_name(f"s43.py.bak_cleanup_bad_guards_{int(time.time())}")
shutil.copy2(TARGET, bak)

lines = TARGET.read_text(encoding="utf-8").splitlines()
out = []

i = 0
removed = 0

def is_bad_marker(s: str) -> bool:
    return (
        "SAFETY_BALANCE_GUARD" in s or
        "SAFETY_MARKET_GUARD" in s or
        "PRE-CALL SAFETY INITIALIZATION" in s or
        "POST-CALL GUARD" in s
    )

while i < len(lines):
    line = lines[i]

    # Remove marker blocks inserted by previous injectors.
    if is_bad_marker(line):
        base_indent = len(line) - len(line.lstrip(" "))
        removed += 1
        i += 1

        # Skip following injected lines until indentation returns to same/lower
        # and the line does not look like part of the injected guard.
        while i < len(lines):
            s = lines[i]
            stripped = s.strip()
            ind = len(s) - len(s.lstrip(" "))

            injected_like = (
                stripped.startswith("bal = 0.0") or
                stripped.startswith("if bal is None") or
                stripped.startswith("elif not isinstance(bal") or
                stripped.startswith("try: bal = float(bal)") or
                stripped.startswith("except: bal = 0.0") or
                stripped.startswith("if not isinstance(stats_map") or
                stripped.startswith("stats_map = {}") or
                stripped.startswith("if not isinstance(by_symbol") or
                stripped.startswith("raise TradingHalt(") or
                is_bad_marker(s)
            )

            if injected_like:
                removed += 1
                i += 1
                continue

            break

        continue

    out.append(line)
    i += 1

TARGET.write_text("\n".join(out) + "\n", encoding="utf-8")

print(f"[OK] backup: {bak}")
print(f"[OK] removed injected/bad guard lines: {removed}")

try:
    py_compile.compile(str(TARGET), doraise=True)
    print("[OK] syntax clean after cleanup")
except py_compile.PyCompileError as e:
    print("[FAIL] syntax still broken after cleanup")
    print(e)

    # Extract line number from error text.
    m = re.search(r'line (\d+)', str(e))
    if m:
        n = int(m.group(1))
        start = max(1, n - 8)
        end = min(len(out), n + 8)
        print("\n--- context ---")
        for idx in range(start, end + 1):
            print(f"{idx}: {out[idx-1]}")
    raise SystemExit(2)
