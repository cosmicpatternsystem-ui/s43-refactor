from pathlib import Path
import py_compile
import shutil
import time
import re

TARGET = Path("s43.py")
bak = TARGET.with_name(f"s43.py.bak_repair_orphan_balance_blocks_{int(time.time())}")
shutil.copy2(TARGET, bak)

lines = TARGET.read_text(encoding="utf-8").splitlines()
out = []
removed = 0
i = 0

def is_float_bal_try_block(pos: int) -> bool:
    if pos + 3 >= len(lines):
        return False
    return (
        lines[pos].strip() == "try:" and
        lines[pos + 1].strip() == "bal = float(bal)" and
        lines[pos + 2].strip().startswith("except") and
        lines[pos + 3].strip() == "bal = 0.0"
    )

while i < len(lines):
    line = lines[i]
    out.append(line)

    if "bal = await self.client.get_balance()" in line:
        i += 1

        # Preserve blank lines, but remove orphan injected float-conversion try blocks
        while i < len(lines):
            if lines[i].strip() == "":
                out.append(lines[i])
                i += 1
                continue

            if is_float_bal_try_block(i):
                removed += 4
                i += 4
                continue

            break

        continue

    i += 1

TARGET.write_text("\n".join(out) + "\n", encoding="utf-8")

print(f"[OK] backup: {bak}")
print(f"[OK] removed orphan balance lines: {removed}")

try:
    py_compile.compile(str(TARGET), doraise=True)
    print("[OK] syntax clean after orphan balance repair")
except py_compile.PyCompileError as e:
    print("[FAIL] syntax still broken")
    print(e)

    m = re.search(r'line (\d+)', str(e))
    if m:
        n = int(m.group(1))
        start = max(1, n - 10)
        end = min(len(out), n + 10)
        print("\n--- context ---")
        for idx in range(start, end + 1):
            print(f"{idx}: {out[idx-1]}")

    raise SystemExit(2)
