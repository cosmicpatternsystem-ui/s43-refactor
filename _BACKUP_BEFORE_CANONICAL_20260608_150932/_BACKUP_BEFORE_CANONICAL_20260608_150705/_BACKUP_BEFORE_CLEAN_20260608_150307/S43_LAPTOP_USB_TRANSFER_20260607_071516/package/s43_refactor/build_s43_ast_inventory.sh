#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

python - <<'PY'
from pathlib import Path

code = r'''#!/usr/bin/env python3
import ast
import hashlib
from collections import defaultdict

TARGET_FILE = "s43.py"
REPORT_FILE = "s43_ast_inventory_report.txt"
SYMBOL_FILE = "s43_symbol_inventory.txt"


def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def safe_lineno(node, default=0):
    return getattr(node, "lineno", default)


def safe_end_lineno(node, default=None):
    v = getattr(node, "end_lineno", None)
    if v is not None:
        return v
    return default if default is not None else safe_lineno(node, 0)


def node_span(node):
    s = safe_lineno(node, 0)
    e = safe_end_lineno(node, s)
    if e < s:
        e = s
    return s, e, e - s + 1


def get_import_names(node):
    names = []
    if isinstance(node, ast.Import):
        for a in node.names:
            names.append(a.name)
    elif isinstance(node, ast.ImportFrom):
        mod = node.module or ""
        if node.level:
            mod = "." * node.level + mod
        for a in node.names:
            names.append(f"{mod}:{a.name}" if mod else a.name)
    return names


def main():
    source = read_text(TARGET_FILE)
    digest = sha256_of_file(TARGET_FILE)
    module = ast.parse(source, filename=TARGET_FILE)

    classes = []
    functions = []
    imports = []
    names = defaultdict(list)

    for node in module.body:
        if isinstance(node, ast.ClassDef):
            s, e, span = node_span(node)
            method_count = 0
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_count += 1
            classes.append((node.name, s, e, span, method_count))
            names[node.name].append(("class", s))

        elif isinstance(node, ast.FunctionDef):
            s, e, span = node_span(node)
            functions.append((node.name, s, e, span, "def"))
            names[node.name].append(("function", s))

        elif isinstance(node, ast.AsyncFunctionDef):
            s, e, span = node_span(node)
            functions.append((node.name, s, e, span, "async def"))
            names[node.name].append(("async_function", s))

        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.extend(get_import_names(node))

    dupes = {k: v for k, v in names.items() if len(v) > 1}

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("AST INVENTORY REPORT\n")
        f.write("====================\n\n")
        f.write(f"Target: {TARGET_FILE}\n")
        f.write(f"SHA256: {digest}\n\n")
        f.write(f"Top-level classes: {len(classes)}\n")
        f.write(f"Top-level functions: {len(functions)}\n")
        f.write(f"Import entries: {len(imports)}\n")
        f.write(f"Duplicate top-level names: {len(dupes)}\n\n")

        f.write("CLASSES\n")
        f.write("-------\n")
        for name, s, e, span, method_count in classes:
            f.write(f"{name}: lines {s}-{e} | span={span} | methods={method_count}\n")

        f.write("\nFUNCTIONS\n")
        f.write("---------\n")
        for name, s, e, span, kind in functions:
            f.write(f"{name}: {kind} | lines {s}-{e} | span={span}\n")

        f.write("\nIMPORTS\n")
        f.write("-------\n")
        for imp in imports:
            f.write(f"{imp}\n")

        f.write("\nDUPLICATE TOP-LEVEL NAMES\n")
        f.write("-------------------------\n")
        if dupes:
            for name, items in sorted(dupes.items()):
                f.write(f"{name}: {items}\n")
        else:
            f.write("None\n")

    with open(SYMBOL_FILE, "w", encoding="utf-8") as f:
        f.write("TOP-LEVEL SYMBOL INVENTORY\n")
        f.write("==========================\n\n")
        for name, items in sorted(names.items()):
            f.write(f"{name}\n")
            for kind, line in items:
                f.write(f"  - {kind} @ line {line}\n")

    print(f"Wrote: {REPORT_FILE}")
    print(f"Wrote: {SYMBOL_FILE}")


if __name__ == "__main__":
    main()
'''
Path("s43_ast_inventory.py").write_text(code, encoding="utf-8")
print("Wrote: s43_ast_inventory.py")
PY

chmod 700 s43_ast_inventory.py
echo "OK"
