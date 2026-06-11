#!/usr/bin/env python3
import ast
from collections import defaultdict
from pathlib import Path

TARGET = Path("s43.py")
TARGET_RUN_INDEX = 2

src = TARGET.read_text(encoding="utf-8", errors="surrogateescape")
tree = ast.parse(src, filename=str(TARGET))

runs = [
    n for n in ast.walk(tree)
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "_run"
]
runs.sort(key=lambda n: (n.lineno, getattr(n, "end_lineno", n.lineno)))

print(f"_run count: {len(runs)}")
if TARGET_RUN_INDEX < 1 or TARGET_RUN_INDEX > len(runs):
    raise SystemExit("ERROR: invalid TARGET_RUN_INDEX")

run_node = runs[TARGET_RUN_INDEX - 1]
print(f"Target _run #{TARGET_RUN_INDEX}: lines {run_node.lineno}-{run_node.end_lineno}")

defs = defaultdict(list)
calls = defaultdict(list)
name_refs = defaultdict(list)
attr_refs = defaultdict(list)

for node in ast.walk(run_node):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node is not run_node:
            defs[node.name].append(node)

    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name):
            calls[f.id].append(node)
        elif isinstance(f, ast.Attribute):
            calls[f.attr].append(node)

    if isinstance(node, ast.Name):
        name_refs[node.id].append(node)

    if isinstance(node, ast.Attribute):
        attr_refs[node.attr].append(node)

print()
print("Nested defs:")
for name in sorted(defs, key=lambda k: defs[k][0].lineno):
    spans = [(d.lineno, getattr(d, "end_lineno", None)) for d in defs[name]]
    call_lines = [getattr(c, "lineno", "?") for c in calls.get(name, [])]
    raw_name_lines = [getattr(n, "lineno", "?") for n in name_refs.get(name, [])]
    attr_lines = [getattr(a, "lineno", "?") for a in attr_refs.get(name, [])]

    real_name_lines = []
    def_lines = {d.lineno for d in defs[name]}
    for n in name_refs.get(name, []):
        if getattr(n, "lineno", None) not in def_lines:
            real_name_lines.append(getattr(n, "lineno", "?"))

    status = "USED"
    if not call_lines and not real_name_lines and not attr_lines:
        status = "LIKELY DEAD"
    elif len(defs[name]) > 1:
        status = "CHECK MULTI-DEF"
    elif not call_lines and (real_name_lines or attr_lines):
        status = "CHECK REF"

    print(f"{status:16} {name:32} defs={spans} calls={call_lines} refs={real_name_lines} attrs={attr_lines}")

print()
print("Likely dead single-def candidates:")
for name in sorted(defs, key=lambda k: defs[k][0].lineno):
    def_lines = {d.lineno for d in defs[name]}
    real_name_lines = [
        getattr(n, "lineno", "?")
        for n in name_refs.get(name, [])
        if getattr(n, "lineno", None) not in def_lines
    ]
    if len(defs[name]) == 1 and not calls.get(name) and not real_name_lines and not attr_refs.get(name):
        d = defs[name][0]
        print(f"- {name}: lines {d.lineno}-{d.end_lineno}")
