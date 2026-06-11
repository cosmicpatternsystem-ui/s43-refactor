from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("s43.py")
text = TARGET.read_text(encoding="utf-8")
lines = text.splitlines()

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
        "ABORT first context mismatch\n"
        f"expected previous line: 'if not s:'\n"
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
        "ABORT second context mismatch\n"
        f"expected previous line: 'except Exception:'\n"
        f"got: {norm(lines[SECOND_DEF - 2])!r}"
    )

backup = TARGET.with_name(
    f"{TARGET.name}.before_fix_nested_short_dupes_final_"
    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
)
shutil.copy2(TARGET, backup)

# Case 1:
# Previous line is:
#   if not s:
# Therefore the nested duplicate def must become the actual fallback:
#   return "-"
indent1 = indent_of(lines[FIRST_DEF - 1])
lines[FIRST_DEF - 1] = indent1 + 'return "-"'
lines[FIRST_DEF] = None

# Case 2:
# Previous line is:
#   except Exception:
# Therefore the except block must not become empty.
# Replace duplicate nested def with:
#   pass
indent2 = indent_of(lines[SECOND_DEF - 1])
lines[SECOND_DEF - 1] = indent2 + "pass"
lines[SECOND_DEF] = None

new_lines = [line for line in lines if line is not None]
TARGET.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

print(f"Backup: {backup}")
print("First nested duplicate converted to: return '-'")
print("Second nested duplicate converted to: pass")
print("Done.")
