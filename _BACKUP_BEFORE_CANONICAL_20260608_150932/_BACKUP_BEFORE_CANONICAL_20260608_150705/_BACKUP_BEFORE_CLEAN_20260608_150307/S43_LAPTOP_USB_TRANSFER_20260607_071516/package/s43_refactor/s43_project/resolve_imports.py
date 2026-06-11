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
