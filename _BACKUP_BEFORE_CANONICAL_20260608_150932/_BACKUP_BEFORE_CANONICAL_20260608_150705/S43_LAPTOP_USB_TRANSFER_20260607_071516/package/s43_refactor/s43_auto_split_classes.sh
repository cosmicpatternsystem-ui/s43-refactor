#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "=== S43 AUTO CLASS SPLITTER ==="

if [ ! -f s43.py ]; then
 echo "ERROR: s43.py not found"
 exit 1
fi

ts=$(date +%Y%m%d_%H%M%S)

echo "[1] backup"
cp s43.py s43_backup_split_$ts.py

mkdir -p s43_project/core

echo "[2] creating splitter"

cat << 'PY' > s43_project/split_classes.py
import ast
from pathlib import Path
import re

SRC = Path("s43.py")
OUT = Path("s43_project/core")

source = SRC.read_text(encoding="utf-8")
tree = ast.parse(source)

OUT.mkdir(parents=True,exist_ok=True)

def to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

classes = []

for node in tree.body:
    if isinstance(node, ast.ClassDef):

        start = node.lineno - 1
        end = node.end_lineno
        code = source.splitlines()[start:end]

        filename = to_snake(node.name) + ".py"
        path = OUT / filename

        with open(path,"w",encoding="utf-8") as f:
            f.write("\n".join(code))

        classes.append((node.name,filename))

init = OUT / "__init__.py"

with open(init,"w",encoding="utf-8") as f:
    for cls,file in classes:
        mod=file.replace(".py","")
        f.write(f"from .{mod} import {cls}\n")

print("classes extracted:",len(classes))
print("output:",OUT)

PY

echo "[3] run splitter"
python s43_project/split_classes.py

echo "[4] files created"
ls s43_project/core | head -20

echo ""
echo "AUTO CLASS SPLIT COMPLETE"
echo "backup: s43_backup_split_$ts.py"

