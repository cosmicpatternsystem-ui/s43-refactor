#!/usr/bin/env python3
import ast
import sys
from pathlib import Path

TARGET = Path("s43.py")
NAME = "top8_panel"
WS_NAME = "_ws_top8_panel"

if not TARGET.exists():
    print("ERROR: s43.py not found.")
    sys.exit(1)

src = TARGET.read_text(encoding="utf-8", errors="surrogateescape")
lines = src.splitlines()

try:
    tree = ast.parse(src, filename=str(TARGET))
except SyntaxError as e:
    print("ERROR: current s43.py has SyntaxError:")
    print(e)
    sys.exit(1)

defs = []
calls = []
name_refs = []
attr_refs = []
ws_refs = []

class ParentMap(ast.NodeVisitor):
    def __init__(self):
        self.parents = {}

    def visit(self, node):
        for child in ast.iter_child_nodes(node):
            self.parents[child] = node
        super().visit(node)

pm = ParentMap()
pm.visit(tree)

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
print()

for fn in defs:
    print(f"=== context: def {NAME}, lines {fn.lineno}-{getattr(fn, 'end_lineno', '?')} ===")
    start = max(1, fn.lineno - 20)
    end = min(len(lines), (getattr(fn, "end_lineno", fn.lineno) or fn.lineno) + 30)
    for i in range(start, end + 1):
        print(f"{i}:{lines[i - 1]}")
    print()

    local_defs = set()
    loaded_names = set()

    for n in ast.walk(fn):
        if isinstance(n, ast.arg):
            local_defs.add(n.arg)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if n is not fn:
                local_defs.add(n.name)
        elif isinstance(n, ast.Name):
            if isinstance(n.ctx, (ast.Store, ast.Del)):
                local_defs.add(n.id)
            elif isinstance(n.ctx, ast.Load):
                loaded_names.add(n.id)

    free_like = sorted(loaded_names - local_defs)
    print(f"=== free-like names used inside {NAME} ===")
    print(", ".join(free_like) if free_like else "(none)")
    print()

external_name_refs = []
for n in name_refs:
    is_definition_name = any(getattr(n, "lineno", None) == d.lineno for d in defs)
    if not is_definition_name:
        external_name_refs.append(n)

print("=== assessment ===")
if len(defs) != 1:
    print("ABORT/INSPECT: expected exactly one definition.")
elif calls:
    print("LIVE: direct call site exists; do not remove.")
elif external_name_refs or attr_refs:
    print("INSPECT: non-call references exist; function may be passed around or referenced indirectly.")
elif ws_refs:
    print("INSPECT: _ws_top8_panel references exist.")
else:
    print("LIKELY DEAD: definition only, no direct calls or references found by AST.")
print("No changes were made to s43.py")
