from pathlib import Path
import re
import shutil
import sys

SRC = "s43.py"   # اگر فایل اصلی‌ات s43_dev_next.py است، این را عوض کن
BAK = SRC + ".bak_top8_compact"

text = Path(SRC).read_text(encoding="utf-8")

if "def top8_compact_panel(" not in text:
    print("ERROR: nested function top8_compact_panel not found")
    sys.exit(1)

if "def _ws_top8_compact_panel(" in text:
    print("ERROR: _ws_top8_compact_panel already exists")
    sys.exit(1)

shutil.copyfile(SRC, BAK)

lines = text.splitlines()

# 1) پیدا کردن nested def
def_line_idx = None
for i, line in enumerate(lines):
    if re.match(r'^\s*def\s+top8_compact_panel\s*\(', line):
        def_line_idx = i
        break

if def_line_idx is None:
    print("ERROR: definition line not found")
    sys.exit(1)

def_line = lines[def_line_idx]
indent = len(def_line) - len(def_line.lstrip(" "))
if indent == 0:
    print("ERROR: top8_compact_panel is not nested; unexpected structure")
    sys.exit(1)

# 2) انتهای تابع nested
end_idx = len(lines)
for j in range(def_line_idx + 1, len(lines)):
    line = lines[j]
    stripped = line.strip()
    cur_indent = len(line) - len(line.lstrip(" "))
    if stripped and cur_indent <= indent:
        end_idx = j
        break

func_block = lines[def_line_idx:end_idx]
if not func_block:
    print("ERROR: failed to capture function block")
    sys.exit(1)

# 3) dedent بدنه و ساخت متد جدید کلاس
dedented = []
for k, line in enumerate(func_block):
    if k == 0:
        dedented.append(re.sub(
            r'^(\s*)def\s+top8_compact_panel\s*\(\s*symbols\s*\)\s*:',
            r'\1def _ws_top8_compact_panel(self, symbols, console, fmt_age_s, fmt_pct):',
            line
        ))
    else:
        if line.startswith(" " * 4):
            dedented.append(line[4:])
        else:
            dedented.append(line)

new_method_block = "\n".join(dedented).rstrip() + "\n"

# 4) پیدا کردن انتهای _run برای درج متد جدید بعد از آن
run_def_idx = None
run_indent = None
for i, line in enumerate(lines):
    if re.match(r'^\s*def\s+_run\s*\(', line):
        run_def_idx = i
        run_indent = len(line) - len(line.lstrip(" "))
        break

if run_def_idx is None:
    print("ERROR: _run not found")
    sys.exit(1)

run_end_idx = len(lines)
for j in range(run_def_idx + 1, len(lines)):
    line = lines[j]
    stripped = line.strip()
    cur_indent = len(line) - len(line.lstrip(" "))
    if stripped and cur_indent <= run_indent:
        run_end_idx = j
        break

# 5) حذف nested function از _run
lines_wo_nested = lines[:def_line_idx] + lines[end_idx:]

# تنظیم run_end_idx بعد از حذف
removed_count = end_idx - def_line_idx
if def_line_idx < run_end_idx:
    run_end_idx -= removed_count

# 6) جایگزینی call site
run_block = lines_wo_nested[run_def_idx:run_end_idx]
run_text = "\n".join(run_block)

before = run_text

# فقط فراخوانی ساده با یک آرگومان را جایگزین می‌کنیم
run_text = re.sub(
    r'(?<!def\s)\btop8_compact_panel\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)',
    r'self._ws_top8_compact_panel(\1, console, fmt_age_s, fmt_pct)',
    run_text
)

if run_text == before:
    print("WARNING: no call site replaced automatically for top8_compact_panel")

new_run_block = run_text.split("\n")
lines_wo_nested = lines_wo_nested[:run_def_idx] + new_run_block + lines_wo_nested[run_end_idx:]

# 7) درج متد جدید بعد از _run
# run_end_idx را دوباره روی نسخه جدید محاسبه می‌کنیم
run_def_idx2 = None
run_indent2 = None
for i, line in enumerate(lines_wo_nested):
    if re.match(r'^\s*def\s+_run\s*\(', line):
        run_def_idx2 = i
        run_indent2 = len(line) - len(line.lstrip(" "))
        break

run_end_idx2 = len(lines_wo_nested)
for j in range(run_def_idx2 + 1, len(lines_wo_nested)):
    line = lines_wo_nested[j]
    stripped = line.strip()
    cur_indent = len(line) - len(line.lstrip(" "))
    if stripped and cur_indent <= run_indent2:
        run_end_idx2 = j
        break

insert_block = [""] + new_method_block.splitlines() + [""]
new_lines = lines_wo_nested[:run_end_idx2] + insert_block + lines_wo_nested[run_end_idx2:]

Path(SRC).write_text("\n".join(new_lines) + "\n", encoding="utf-8")

print("OK: patched", SRC)
print("BACKUP:", BAK)
print("")
print("NEXT:")
print("  python -m py_compile", SRC)
print("  grep -n \"_ws_top8_compact_panel\\|top8_compact_panel(\"", SRC)
