#!/usr/bin/env python3
import ast
from pathlib import Path

TARGET = Path("s43.py")
TARGET_RUN_INDEX = 2
WATCH = {"_short", "_assets_detail"}

src = TARGET.read_text(encoding="utf-8", errors="surrogateescape")
tree = ast.parse(src, filename=str(TARGET))

runs = [
    n for n in ast.walk(tree)
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "_run"
]
runs.sort(key=lambda n: (n.lineno, getattr(n, "end_lineno", n.lineno)))
run_node = runs[TARGET_RUN_INDEX - 1]

parent = {}
for node in ast.walk(run_node):
    for child in ast.iter_child_nodes(node):
        parent[child] = node

def parent_func_chain(node):
    chain = []
    cur = parent.get(node)
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            chain.append((cur.name, cur.lineno, getattr(cur, "end_lineno", None)))
        cur = parent.get(cur)
    return chain

print(f"Target _run #{TARGET_RUN_INDEX}: {run_node.lineno}-{run_node.end_lineno}")
print()

for node in ast.walk(run_node):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in WATCH:
        args = [a.arg for a in node.args.args]
        defaults = len(node.args.defaults)
        print(f"DEF {node.name} lines {node.lineno}-{node.end_lineno} args={args} defaults={defaults}")
        chain = parent_func_chain(node)
        print("  parent chain:")
        for item in chain:
            print(f"    - {item[0]} lines {item[1]}-{item[2]}")
        print()
