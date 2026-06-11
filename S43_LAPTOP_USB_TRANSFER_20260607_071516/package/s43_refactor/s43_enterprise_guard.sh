#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "== S43 Enterprise Code Guard =="

TS=$(date +%Y%m%d_%H%M%S)

cat > s43_enterprise_guard.py <<'PY'
#!/usr/bin/env python3

import re
import ast
import hashlib
import time
from pathlib import Path

ROOT = Path(".")
TS = time.strftime("%Y%m%d_%H%M%S")

unicode_patterns = {
    "persian_arabic": re.compile(r"[\u0600-\u06FF]"),
    "rtl_marks": re.compile(r"[\u200F\u202A-\u202E]"),
    "zero_width": re.compile(r"[\u200B\u200C\u200D]"),
}

report_file = Path(f"s43_enterprise_report_{TS}.txt")

issues = []

def scan_unicode():
    for path in ROOT.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except:
            continue

        lines = text.splitlines()

        for i, line in enumerate(lines,1):
            for name, pattern in unicode_patterns.items():
                if pattern.search(line):
                    issues.append(
                        f"{path}:{i} [unicode:{name}] {line.strip()}"
                    )

def compute_hash():
    target = Path("s43.py")

    if not target.exists():
        issues.append("s43.py not found")
        return

    data = target.read_bytes()
    h = hashlib.sha256(data).hexdigest()

    issues.append(f"s43.py sha256: {h}")

def syntax_check():
    try:
        ast.parse(Path("s43.py").read_text())
        issues.append("syntax_check: OK")
    except Exception as e:
        issues.append(f"syntax_error: {e}")

def duplicate_functions():
    funcs = {}
    target = Path("s43.py")

    if not target.exists():
        return

    tree = ast.parse(target.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name
            line = node.lineno

            if name in funcs:
                issues.append(
                    f"duplicate_function: {name} line {line}"
                )
            else:
                funcs[name] = line

def dead_code_scan():
    target = Path("s43.py")

    if not target.exists():
        return

    lines = target.read_text().splitlines()

    for i,l in enumerate(lines,1):
        if "if False:" in l or "if 0:" in l:
            issues.append(
                f"dead_code_pattern line {i}"
            )

scan_unicode()
compute_hash()
syntax_check()
duplicate_functions()
dead_code_scan()

with report_file.open("w",encoding="utf-8") as f:
    for i in issues:
        f.write(i+"\n")

print("ENTERPRISE SCAN COMPLETE")
print("Total findings:",len(issues))
print("Report:",report_file)
PY

chmod +x s43_enterprise_guard.py

echo "[1/2] Running enterprise scan..."
python s43_enterprise_guard.py

echo "[2/2] Compile verification..."
python -m py_compile s43.py

echo ""
echo "== ENTERPRISE GUARD ACTIVE =="

echo "Run manual scan anytime:"
echo "python s43_enterprise_guard.py"

