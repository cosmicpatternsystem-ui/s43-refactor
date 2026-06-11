from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("s43.py")
text = TARGET.read_text(encoding="utf-8")
lines = text.splitlines()

# Current line numbers after restore:
FIRST_DEF = 24986
SECOND_DEF = 25369

sig1 = "def _short(s: str, n: int = 42) -> str:"
sig2 = "def _short(s: str, n: int = 28) -> str:"
ret = "return _short_text(s, n=n, empty='-', strip=True, collapse_ws=True, ellipsis='...')"

def norm(s: str) -> str:
    return s.strip()

def indent_of(s: str) -> str:
    return s[:len(s) - len(s.lstrip(" "))]

# Validate first duplicate
if norm(lines[FIRST_DEF - 1]) != sig1:
    raise SystemExit(
        f"ABORT first def mismatch at {FIRST_DEF}\n"
        f"got: {norm(lines[FIRST_DEF - 1])!r}"
    )
if norm(lines[FIRST_DEF]) != ret:
    raise SystemExit(
        f"ABORT first return mismatch at {FIRST_DEF + 1}\n"
        f"got: {norm(lines[FIRST_DEF])!r}"
    )
if norm(lines[FIRST_DEF - 2]) != "if not s:":
    raise SystemExit(
        f"ABORT first context mismatch: expected previous line to be 'if not s:'\n"
        f"got: {norm(lines[FIRST_DEF - 2])!r}"
    )

# Validate second duplicate
if norm(lines[SECOND_DEF - 1]) != sig2:
    raise SystemExit(
        f"ABORT second def mismatch at {SECOND_DEF}\n"
        f"got: {norm(lines[SECOND_DEF - 1])!r}"
    )
if norm(lines[SECOND_DEF]) != ret:
    raise SystemExit(
        f"ABORT second return mismatch at {SECOND_DEF + 1}\n"
        f"got: {norm(lines[SECOND_DEF])!r}"
    )
if norm(lines[SECOND_DEF - 2]) != "except Exception:":
    raise SystemExit(
        f"ABORT second context mismatch: expected previous line to be 'except Exception:'\n"
        f"got: {norm(lines[SECOND_DEF - 2])!r}"
    )

backup = TARGET.with_name(
    f"{TARGET.name}.before_fix_nested_short_dupes_proper_"
    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
)
shutil.copy2(TARGET, backup)

# First duplicate:
# It is the only body under:
#   if not s:
# So replace the duplicate def line with:
#   return "-"
# and remove its nested return line.
first_indent = indent_of(lines[FIRST_DEF - 1])
lines[FIRST_DEF - 1] = first_indent + 'return "-"'
lines[FIRST_DEF] = None

# Second duplicate:
# It is inside except Exception, but the except block has following fallback code:
#   if not s:
#       return "-"
# So remove only these two duplicate lines.
lines[SECOND_DEF - 1] = None
lines[SECOND_DEF] = None

new_lines = [line for line in lines if line is not None]
TARGET.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

print(f"Backup: {backup}")
print("Fixed first nested duplicate by replacing with return '-'")
print("Removed second nested duplicate")
print("Done.")
