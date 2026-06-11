#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "=== S43 DEPENDENCY RESOLVER ==="

CORE="s43_project/core"

if [ ! -d "$CORE" ]; then
 echo "ERROR: core folder not found"
 exit 1
fi

cat << 'PY' > s43_project/resolve_imports.py
import os
import re
from pathlib import Path

CORE = Path("s43_project/core")

files = list(CORE.glob("*.py"))

class_map = {}

for f in files:
    if f.name == "__init__.py":
        continue
    text = f.read_text(encoding="utf-8")
    m = re.search(r'class\s+([A-Za-z0-9_]+)', text)
    if m:
        class_map[m.group(1)] = f.name.replace(".py","")

for f in files:

    if f.name == "__init__.py":
        continue

    text = f.read_text(encoding="utf-8")

    imports = []
    for cls,mod in class_map.items():

        if cls in text and mod+".py" != f.name:
            imp = f"from .{mod} import {cls}"
            if imp not in text:
                imports.append(imp)

    if imports:
        new_text = "\n".join(imports) + "\n\n" + text
        f.write_text(new_text,encoding="utf-8")
        print("updated:",f.name)

print("dependency resolution complete")
PY

echo "[1] resolving imports"
python s43_project/resolve_imports.py

echo "[2] done"

