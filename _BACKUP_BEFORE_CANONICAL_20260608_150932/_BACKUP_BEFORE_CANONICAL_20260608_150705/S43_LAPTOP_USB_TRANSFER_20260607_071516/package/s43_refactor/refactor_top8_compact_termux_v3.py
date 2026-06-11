from pathlib import Path
import re
import shutil
import sys

SRC = "s43.py"
BAK = SRC + ".bak_top8_compact_v3"

p = Path(SRC)
if not p.exists():
    print("ERROR: file not found:", SRC)
    sys.exit(1)

text = p.read_text(encoding="utf-8")
lines = text.splitlines()

if "def top8_compact_panel(" not in text:
    print("ERROR: nested function top8_compact_panel not found")
    sys.exit(1)

if "def _ws_top8_compact_panel(" in text:
    print("ERROR: _ws_top8_compact_panel already exists")
    sys.exit(1)

shutil.copyfile(SRC, BAK)

# ------------------------------------------------------------
# 1) پیدا کردن nested def top8_compact_panel
# ------------------------------------------------------------
def_line_idx = None
for i, line in enumerate(lines):
    if re.match(r'^\s*def\s+top8_compact_panel\s*\(', line):
        def_line_idx = i
        break

if def_line_idx is None:
    print("ERROR: definition line not found")
    sys.exit(1)

def_line = lines[def_line_idx]
nested_indent = len(def_line) - len(def_line.lstrip(" "))

if nested_indent == 0:
    print("ERROR: top8_compact_panel is not nested; unexpected structure")
    sys.exit(1)

print("FOUND top8_compact_panel at line", def_line_idx + 1, "indent", nested_indent)

# ------------------------------------------------------------
# 2) پیدا کردن تابع/متد والد واقعی
#    نزدیک‌ترین def/async def قبلی با indent کمتر
# ------------------------------------------------------------
parent_def_idx = None
parent_indent = None
parent_name = None

for i in range(def_line_idx - 1, -1, -1):
    line = lines[i]
    m = re.match(r'^(\s*)(async\s+def|def)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', line)
    if not m:
        continue

    cur_indent = len(m.group(1))
    if cur_indent < nested_indent:
        parent_def_idx = i
        parent_indent = cur_indent
        parent_name = m.group(3)
        break

if parent_def_idx is None:
    print("ERROR: parent function/method not found")
    sys.exit(1)

print("FOUND parent:", parent_name, "at line", parent_def_idx + 1, "indent", parent_indent)

# ------------------------------------------------------------
# 3) پیدا کردن انتهای parent
# ------------------------------------------------------------
parent_end_idx = len(lines)
for j in range(parent_def_idx + 1, len(lines)):
    line = lines[j]
    stripped = line.strip()
    cur_indent = len(line) - len(line.lstrip(" "))
    if stripped and cur_indent <= parent_indent:
        parent_end_idx = j
        break

print("PARENT range:", parent_def_idx + 1, "to", parent_end_idx)

if not (parent_def_idx < def_line_idx < parent_end_idx):
    print("ERROR: compact function is not inside detected parent range")
    print("parent:", parent_def_idx + 1, parent_end_idx)
    print("compact:", def_line_idx + 1)
    sys.exit(1)

# ------------------------------------------------------------
# 4) پیدا کردن انتهای nested top8_compact_panel
# ------------------------------------------------------------
end_idx = len(lines)
for j in range(def_line_idx + 1, len(lines)):
    line = lines[j]
    stripped = line.strip()
    cur_indent = len(line) - len(line.lstrip(" "))
    if stripped and cur_indent <= nested_indent:
        end_idx = j
        break

func_block = lines[def_line_idx:end_idx]

if not func_block:
    print("ERROR: failed to capture function block")
    sys.exit(1)

print("CAPTURED compact function lines:", def_line_idx + 1, "to", end_idx)

# ------------------------------------------------------------
# 5) ساخت متد جدید کلاس
#    nested indent معمولاً 8 است، متد کلاس باید 4 باشد
#    پس یک سطح، یعنی 4 space، کم می‌کنیم.
# ------------------------------------------------------------
class_method_indent_count = max(0, nested_indent - 4)
class_method_indent = " " * class_method_indent_count

dedented = []
for k, line in enumerate(func_block):
    if k == 0:
        dedented.append(
            class_method_indent +
            "def _ws_top8_compact_panel(self, symbols, console, fmt_age_s, fmt_pct):"
        )
    else:
        if line.startswith(" " * 4):
            dedented.append(line[4:])
        else:
            dedented.append(line)

new_method_block = "\n".join(dedented).rstrip() + "\n"

# ------------------------------------------------------------
# 6) حذف nested function از parent
# ------------------------------------------------------------
lines_wo_nested = lines[:def_line_idx] + lines[end_idx:]

removed_count = end_idx - def_line_idx
if def_line_idx < parent_end_idx:
    parent_end_idx -= removed_count

# ------------------------------------------------------------
# 7) جایگزینی call site داخل parent
# ------------------------------------------------------------
parent_block = lines_wo_nested[parent_def_idx:parent_end_idx]
parent_text = "\n".join(parent_block)
before = parent_text

# حالت ساده: top8_compact_panel(symbols)
parent_text = re.sub(
    r'(?<!def\s)\btop8_compact_panel\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)',
    r'self._ws_top8_compact_panel(\1, console, fmt_age_s, fmt_pct)',
    parent_text
)

# حالت بازتر: top8_compact_panel(expr بدون پرانتز تو در تو)
if "top8_compact_panel(" in parent_text:
    parent_text = re.sub(
        r'(?<!def\s)\btop8_compact_panel\s*\(\s*([^()\n]+?)\s*\)',
        r'self._ws_top8_compact_panel(\1, console, fmt_age_s, fmt_pct)',
        parent_text
    )

if parent_text == before:
    print("WARNING: no call site replaced automatically for top8_compact_panel")
else:
    print("OK: call site replacement attempted")

new_parent_block = parent_text.split("\n")
lines_wo_nested = (
    lines_wo_nested[:parent_def_idx]
    + new_parent_block
    + lines_wo_nested[parent_end_idx:]
)

# ------------------------------------------------------------
# 8) پیدا کردن دوباره parent و انتهای آن بعد از تغییر
# ------------------------------------------------------------
parent_def_idx2 = None
parent_indent2 = None

# با همان نام parent، از حوالی قبلی پیدا کن
for i, line in enumerate(lines_wo_nested):
    m = re.match(r'^(\s*)(async\s+def|def)\s+' + re.escape(parent_name) + r'\s*\(', line)
    if m:
        cur_indent = len(m.group(1))
        if cur_indent == parent_indent:
            parent_def_idx2 = i
            parent_indent2 = cur_indent
            break

if parent_def_idx2 is None:
    print("ERROR: parent disappeared after edit")
    sys.exit(1)

parent_end_idx2 = len(lines_wo_nested)
for j in range(parent_def_idx2 + 1, len(lines_wo_nested)):
    line = lines_wo_nested[j]
    stripped = line.strip()
    cur_indent = len(line) - len(line.lstrip(" "))
    if stripped and cur_indent <= parent_indent2:
        parent_end_idx2 = j
        break

# ------------------------------------------------------------
# 9) درج متد جدید بعد از parent
# ------------------------------------------------------------
insert_block = [""] + new_method_block.splitlines() + [""]

new_lines = (
    lines_wo_nested[:parent_end_idx2]
    + insert_block
    + lines_wo_nested[parent_end_idx2:]
)

new_text = "\n".join(new_lines) + "\n"
p.write_text(new_text, encoding="utf-8")

print("")
print("OK: patched", SRC)
print("BACKUP:", BAK)
print("PARENT:", parent_name)
print("")
print("NEXT:")
print("  python -m py_compile", SRC)
print("  grep -n \"_ws_top8_compact_panel\\|top8_compact_panel(\"", SRC)
