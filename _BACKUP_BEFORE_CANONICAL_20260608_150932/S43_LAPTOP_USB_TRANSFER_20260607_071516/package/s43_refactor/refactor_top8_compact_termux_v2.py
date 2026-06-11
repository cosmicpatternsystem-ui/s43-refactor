from pathlib import Path
import re
import shutil
import sys

SRC = "s43.py"
BAK = SRC + ".bak_top8_compact_v2"

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

# backup
shutil.copyfile(SRC, BAK)

# -----------------------------
# 1) پیدا کردن nested def top8_compact_panel
# -----------------------------
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

# -----------------------------
# 2) پیدا کردن انتهای تابع nested
# -----------------------------
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

print("CAPTURED function lines:", def_line_idx + 1, "to", end_idx)

# -----------------------------
# 3) ساخت متد جدید کلاس
#    یک سطح indent کم می‌کنیم
# -----------------------------
dedented = []
for k, line in enumerate(func_block):
    if k == 0:
        # حفظ indent کلاس: nested_indent - 4
        class_method_indent = " " * max(0, nested_indent - 4)
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

# -----------------------------
# 4) پیدا کردن _run
#    پشتیبانی از def و async def
# -----------------------------
run_def_idx = None
run_indent = None

for i, line in enumerate(lines):
    if re.match(r'^\s*(async\s+def|def)\s+_run\s*\(', line):
        run_def_idx = i
        run_indent = len(line) - len(line.lstrip(" "))
        break

if run_def_idx is None:
    print("ERROR: _run not found")
    print("DEBUG: nearby candidates:")
    for i, line in enumerate(lines):
        if "_run" in line:
            print(i + 1, ":", line[:160])
    sys.exit(1)

print("FOUND _run at line", run_def_idx + 1, "indent", run_indent)

# -----------------------------
# 5) پیدا کردن انتهای _run
# -----------------------------
run_end_idx = len(lines)
for j in range(run_def_idx + 1, len(lines)):
    line = lines[j]
    stripped = line.strip()
    cur_indent = len(line) - len(line.lstrip(" "))
    if stripped and cur_indent <= run_indent:
        run_end_idx = j
        break

print("RUN range:", run_def_idx + 1, "to", run_end_idx)

# sanity: تابع compact باید داخل _run باشد
if not (run_def_idx < def_line_idx < run_end_idx):
    print("ERROR: top8_compact_panel is not inside _run range")
    print("run:", run_def_idx + 1, run_end_idx)
    print("compact:", def_line_idx + 1)
    sys.exit(1)

# -----------------------------
# 6) حذف nested function
# -----------------------------
lines_wo_nested = lines[:def_line_idx] + lines[end_idx:]

removed_count = end_idx - def_line_idx
if def_line_idx < run_end_idx:
    run_end_idx -= removed_count

# -----------------------------
# 7) جایگزینی call site داخل _run
# -----------------------------
run_block = lines_wo_nested[run_def_idx:run_end_idx]
run_text = "\n".join(run_block)
before = run_text

# حالت ساده: top8_compact_panel(symbols)
run_text = re.sub(
    r'(?<!def\s)\btop8_compact_panel\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)',
    r'self._ws_top8_compact_panel(\1, console, fmt_age_s, fmt_pct)',
    run_text
)

# حالت کمی بازتر: top8_compact_panel(anything_without_nested_paren)
# اگر هنوز چیزی باقی مانده بود، تلاش دوم
if "top8_compact_panel(" in run_text:
    run_text = re.sub(
        r'(?<!def\s)\btop8_compact_panel\s*\(\s*([^()\n]+?)\s*\)',
        r'self._ws_top8_compact_panel(\1, console, fmt_age_s, fmt_pct)',
        run_text
    )

if run_text == before:
    print("WARNING: no call site replaced automatically for top8_compact_panel")
else:
    print("OK: call site replacement attempted")

new_run_block = run_text.split("\n")
lines_wo_nested = lines_wo_nested[:run_def_idx] + new_run_block + lines_wo_nested[run_end_idx:]

# -----------------------------
# 8) پیدا کردن انتهای _run دوباره
# -----------------------------
run_def_idx2 = None
run_indent2 = None

for i, line in enumerate(lines_wo_nested):
    if re.match(r'^\s*(async\s+def|def)\s+_run\s*\(', line):
        run_def_idx2 = i
        run_indent2 = len(line) - len(line.lstrip(" "))
        break

if run_def_idx2 is None:
    print("ERROR: _run disappeared after edit")
    sys.exit(1)

run_end_idx2 = len(lines_wo_nested)
for j in range(run_def_idx2 + 1, len(lines_wo_nested)):
    line = lines_wo_nested[j]
    stripped = line.strip()
    cur_indent = len(line) - len(line.lstrip(" "))
    if stripped and cur_indent <= run_indent2:
        run_end_idx2 = j
        break

# -----------------------------
# 9) درج متد جدید بعد از _run
# -----------------------------
insert_block = [""] + new_method_block.splitlines() + [""]
new_lines = lines_wo_nested[:run_end_idx2] + insert_block + lines_wo_nested[run_end_idx2:]

new_text = "\n".join(new_lines) + "\n"
p.write_text(new_text, encoding="utf-8")

print("")
print("OK: patched", SRC)
print("BACKUP:", BAK)
print("")
print("NEXT:")
print("  python -m py_compile", SRC)
print("  grep -n \"_ws_top8_compact_panel\\|top8_compact_panel(\"", SRC)
