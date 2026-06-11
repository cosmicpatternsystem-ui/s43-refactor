#!/usr/bin/env python3
import ast
import shutil
import subprocess
import sys
import time
from pathlib import Path

TARGET = Path("s43.py")
TARGET_RUN_INDEX = 2
REMOVE = ["fmt_mid", "_tail_warn_err_lines", "_crashlog_tail"]

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

runs = []
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_run":
        runs.append(node)

runs.sort(key=lambda n: (n.lineno, getattr(n, "end_lineno", n.lineno)))

if TARGET_RUN_INDEX < 1 or TARGET_RUN_INDEX > len(runs):
    print("ERROR: invalid TARGET_RUN_INDEX")
    sys.exit(1)

run_node = runs[TARGET_RUN_INDEX - 1]

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

targets = []

for name in REMOVE:
    defs, calls, name_refs, attr_refs = collect_usage(run_node, name)

    print(f"--- {name} ---")
    print(f"defs={[(d.lineno, getattr(d, 'end_lineno', None)) for d in defs]}")
    print(f"calls={[getattr(c, 'lineno', '?') for c in calls]}")
    print(f"name_refs={[getattr(n, 'lineno', '?') for n in name_refs]}")
    print(f"attr_refs={[getattr(a, 'lineno', '?') for a in attr_refs]}")

    real_name_refs = []
    for n in name_refs:
        if not (hasattr(n, "lineno") and len(defs) == 1 and n.lineno == defs[0].lineno):
            real_name_refs.append(n)

    if len(defs) != 1:
        print("ABORT: expected exactly one def")
        sys.exit(1)
    if getattr(defs[0], "end_lineno", None) is None:
        print("ABORT: no end_lineno support")
        sys.exit(1)
    if calls:
        print("ABORT: call site exists")
        sys.exit(1)
    if real_name_refs:
        print("ABORT: extra name refs exist")
        sys.exit(1)
    if attr_refs:
        print("ABORT: attr refs exist")
        sys.exit(1)

    fn = defs[0]
    targets.append((name, fn.lineno, fn.end_lineno))

targets.sort(key=lambda x: x[1], reverse=True)

stamp = time.strftime("%Y%m%d_%H%M%S")
backup = TARGET.with_name(f"s43.py.before_remove_dead_batch1_{stamp}")
shutil.copy2(TARGET, backup)
print(f"Backup: {backup}")

new_lines = lines[:]
for name, start, end in targets:
    print(f"Removing {name}: lines {start}-{end}")
    new_lines = new_lines[:start - 1] + new_lines[end:]

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

print("OK: batch1 removed and s43.py compiles.")
