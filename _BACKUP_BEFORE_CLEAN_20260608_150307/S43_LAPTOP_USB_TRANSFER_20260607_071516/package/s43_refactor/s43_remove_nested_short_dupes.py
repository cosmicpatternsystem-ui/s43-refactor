from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("s43.py")
text = TARGET.read_text(encoding="utf-8")
lines = text.splitlines()

# line numbers are 1-based, inclusive
# remove only these exact duplicate nested defs:
# 24835: def _short(s: str, n: int = 42) -> str:
# 25332: def _short(s: str, n: int = 28) -> str:
#
# based on inspected context, each duplicate is a 2-line block:
#   def _short(...):
#       return _short_text(...)
#
# convert to 0-based slices
to_remove = [
    (24835, 24836),
    (25332, 25333),
]

# validate exact content before modifying
expected = {
    24835: "def _short(s: str, n: int = 42) -> str:",
    24836: "return _short_text(s, n=n, empty='-', strip=True, collapse_ws=True, ellipsis='...')",
    25332: "def _short(s: str, n: int = 28) -> str:",
    25333: "return _short_text(s, n=n, empty='-', strip=True, collapse_ws=True, ellipsis='...')",
}

def norm(s: str) -> str:
    return s.strip()

for ln, exp in expected.items():
    got = lines[ln - 1]
    if norm(got) != exp:
        raise SystemExit(
            f"ABORT: line {ln} mismatch\n"
            f"expected: {exp!r}\n"
            f"got     : {got.strip()!r}"
        )

backup = TARGET.with_name(f"{TARGET.name}.before_remove_nested_short_dupes_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
shutil.copy2(TARGET, backup)

remove_idx = set()
for a, b in to_remove:
    for i in range(a - 1, b):
        remove_idx.add(i)

new_lines = [line for i, line in enumerate(lines) if i not in remove_idx]
TARGET.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

print(f"Backup: {backup}")
print(f"Removed blocks: {to_remove}")
print("Done.")
