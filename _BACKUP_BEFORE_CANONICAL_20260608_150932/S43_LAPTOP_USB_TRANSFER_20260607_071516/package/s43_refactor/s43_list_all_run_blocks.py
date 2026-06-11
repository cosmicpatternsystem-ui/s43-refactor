#!/usr/bin/env python3
import ast
import sys
from pathlib import Path

TARGET = Path("s43.py")

if not TARGET.exists():
    print("ERROR: s43.py not found.")
    sys.exit(1)

src = TARGET.read_text(encoding="utf-8", errors="surrogateescape")

try:
    tree = ast.parse(src, filename=str(TARGET))
except SyntaxError as e:
    print("ERROR: s43.py has SyntaxError:")
    print(e)
    sys.exit(1)

runs = []
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_run":
        runs.append(node)

runs.sort(key=lambda n: (n.lineno, getattr(n, "end_lineno", n.lineno)))

print(f"total _run defs: {len(runs)}")
print("=" * 100)

for idx, run in enumerate(runs, 1):
    nested = []
    for child in run.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nested.append(child)

    print(f"[{idx}] _run lines {run.lineno}-{getattr(run, 'end_lineno', '?')}")
    print(f"    direct nested defs: {len(nested)}")
    for fn in nested:
        size = None
        if getattr(fn, "end_lineno", None) is not None:
            size = fn.end_lineno - fn.lineno + 1
        print(f"      - {fn.name}: lines {fn.lineno}-{getattr(fn, 'end_lineno', '?')} size={size}")
    print("-" * 100)
