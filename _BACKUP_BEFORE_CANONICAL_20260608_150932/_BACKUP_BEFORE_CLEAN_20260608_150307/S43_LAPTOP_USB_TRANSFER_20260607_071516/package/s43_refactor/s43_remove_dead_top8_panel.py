#!/usr/bin/env python3
import ast
import shutil
import subprocess
import sys
import time
from pathlib import Path

TARGET = Path("s43.py")
NAME = "top8_panel"
WS_NAME = "_ws_top8_panel"

if not TARGET.exists():
    print("ERROR: s43.py not found.")
    sys.exit(1)

src = TARGET.read_text(encoding="utf-8", errors="surrogateescape")
lines = src.splitlines(keepends=True)

try:
    tree = ast.parse(src, filename=str(TARGET))
except SyntaxError as e:
    print("ERROR: current s43.py has SyntaxError before patch:")
    print(e)
    sys.exit(1)

defs = []
calls = []
name_refs = []
attr_refs = []
ws_refs = []

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == NAME:
        defs.append(node)

    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name) and f.id == NAME:
            calls.append(node)
        elif isinstance(f, ast.Attribute) and f.attr == NAME:
            calls.append(node)

    if isinstance(node, ast.Name) and node.id == NAME:
        name_refs.append(node)

    if isinstance(node, ast.Attribute) and node.attr == NAME:
        attr_refs.append(node)

    if isinstance(node, ast.Name) and node.id == WS_NAME:
        ws_refs.append(node)
    elif isinstance(node, ast.Attribute) and node.attr == WS_NAME:
        ws_refs.append(node)

print(f"defs({NAME})={[(d.lineno, getattr(d, 'end_lineno', None)) for d in defs]}")
print(f"calls({NAME})={[getattr(c, 'lineno', '?') for c in calls]}")
print(f"name_refs({NAME})={[getattr(n, 'lineno', '?') for n in name_refs]}")
print(f"attr_refs(.{NAME})={[getattr(n, 'lineno', '?') for n in attr_refs]}")
print(f"refs({WS_NAME})={[getattr(n, 'lineno', '?') for n in ws_refs]}")

if len(defs) != 1:
    print("ABORT: expected exactly one function definition.")
    sys.exit(1)

fn = defs[0]
if getattr(fn, "end_lineno", None) is None:
    print("ABORT: Python AST has no end_lineno support.")
    sys.exit(1)

if calls:
    print("ABORT: real call site exists; not removing.")
    sys.exit(1)

if name_refs:
    print("ABORT: name references exist; inspect first.")
    sys.exit(1)

if attr_refs:
    print("ABORT: attribute references exist; inspect first.")
    sys.exit(1)

if ws_refs:
    print("ABORT: _ws_top8_panel references exist; inspect first.")
    sys.exit(1)

start = fn.lineno
end = fn.end_lineno

print(f"Removing lines {start}-{end}")

stamp = time.strftime("%Y%m%d_%H%M%S")
backup = TARGET.with_name(f"s43.py.before_remove_dead_top8_panel_{stamp}")
shutil.copy2(TARGET, backup)
print(f"Backup: {backup}")

new_lines = lines[:start - 1] + lines[end:]
TARGET.write_text("".join(new_lines), encoding="utf-8", errors="surrogateescape")

res = subprocess.run(
    [sys.executable, "-m", "py_compile", str(TARGET)],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

if res.returncode != 0:
    print("ERROR: py_compile failed after removal. Rolling back.")
    print(res.stdout)
    shutil.copy2(backup, TARGET)

    rb = subprocess.run(
        [sys.executable, "-m", "py_compile", str(TARGET)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if rb.returncode == 0:
        print("Rollback OK: original file restored and compiles.")
    else:
        print("Rollback problem:")
        print(rb.stdout)

    sys.exit(1)

print("OK: dead top8_panel removed and s43.py compiles.")
print("Post-check grep:")
found = False
for i, line in enumerate(TARGET.read_text(encoding="utf-8", errors="surrogateescape").splitlines(), 1):
    if NAME in line or WS_NAME in line:
        found = True
        print(f"{i}:{line}")

if not found:
    print("No remaining top8_panel references found.")
