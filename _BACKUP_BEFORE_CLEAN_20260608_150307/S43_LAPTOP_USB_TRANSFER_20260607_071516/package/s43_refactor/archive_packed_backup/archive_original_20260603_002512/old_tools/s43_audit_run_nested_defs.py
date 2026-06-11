#!/usr/bin/env python3
import ast
import sys
from pathlib import Path

TARGET = Path("s43.py")
RUN_NAME = "_run"

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

run_node = None
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == RUN_NAME:
        run_node = node
        break

if run_node is None:
    print("ERROR: _run not found.")
    sys.exit(1)

nested_defs = []
for node in run_node.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        nested_defs.append(node)

def collect_usage(scope_node, target_name):
    defs = []
    calls = []
    name_refs = []
    attr_refs = []

    for node in ast.walk(scope_node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == target_name:
            defs.append(node)

        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id == target_name:
                calls.append(node)
            elif isinstance(f, ast.Attribute) and f.attr == target_name:
                calls.append(node)

        if isinstance(node, ast.Name) and node.id == target_name:
            name_refs.append(node)

        if isinstance(node, ast.Attribute) and node.attr == target_name:
            attr_refs.append(node)

    return defs, calls, name_refs, attr_refs

print(f"_run at lines {run_node.lineno}-{getattr(run_node, 'end_lineno', '?')}")
print(f"top-level nested defs in _run: {len(nested_defs)}")
print("-" * 100)

for fn in nested_defs:
    defs, calls, name_refs, attr_refs = collect_usage(run_node, fn.name)

    def_lines = [(d.lineno, getattr(d, "end_lineno", None)) for d in defs]
    call_lines = [getattr(c, "lineno", "?") for c in calls]
    name_lines = [getattr(n, "lineno", "?") for n in name_refs]
    attr_lines = [getattr(a, "lineno", "?") for a in attr_refs]

    real_name_refs = [ln for ln in name_lines if ln != fn.lineno]
    status = "LIVE"
    if len(defs) == 1 and not call_lines and not real_name_refs and not attr_lines:
        status = "LIKELY DEAD"

    size = None
    if getattr(fn, "end_lineno", None) is not None:
        size = fn.end_lineno - fn.lineno + 1

    print(f"name={fn.name}")
    print(f"  lines={fn.lineno}-{getattr(fn, 'end_lineno', '?')} size={size}")
    print(f"  defs={def_lines}")
    print(f"  calls={call_lines}")
    print(f"  name_refs={name_lines}")
    print(f"  attr_refs={attr_lines}")
    print(f"  status={status}")
    print("-" * 100)
