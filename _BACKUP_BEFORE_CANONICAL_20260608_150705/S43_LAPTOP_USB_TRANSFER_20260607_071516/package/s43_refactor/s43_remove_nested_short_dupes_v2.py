from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("s43.py")
text = TARGET.read_text(encoding="utf-8")
lines = text.splitlines()

targets = [
    (24986, "def _short(s: str, n: int = 42) -> str:"),
    (25369, "def _short(s: str, n: int = 28) -> str:"),
]
ret = "return _short_text(s, n=n, empty='-', strip=True, collapse_ws=True, ellipsis='...')"

def norm(s: str) -> str:
    return s.strip()

for ln, sig in targets:
    got = norm(lines[ln - 1])
    if got != sig:
        raise SystemExit(
            f"ABORT def mismatch at line {ln}\n"
            f"expected: {sig!r}\n"
            f"got     : {got!r}"
        )
    got2 = norm(lines[ln])
    if got2 != ret:
        raise SystemExit(
            f"ABORT return mismatch at line {ln+1}\n"
            f"expected: {ret!r}\n"
            f"got     : {got2!r}"
        )

backup = TARGET.with_name(
    f"{TARGET.name}.before_remove_nested_short_dupes_v2_"
    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
)
shutil.copy2(TARGET, backup)

remove_idx = set()
for ln, _ in targets:
    remove_idx.add(ln - 1)  # def line
    remove_idx.add(ln)      # return line

new_lines = [line for i, line in enumerate(lines) if i not in remove_idx]
TARGET.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

print(f"Backup: {backup}")
print("Removed nested duplicate _short defs at:", [ln for ln, _ in targets])
print("Done.")
