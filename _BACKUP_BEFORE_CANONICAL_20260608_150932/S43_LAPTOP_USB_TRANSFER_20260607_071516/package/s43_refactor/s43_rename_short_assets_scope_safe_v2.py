#!/usr/bin/env python3
import ast
import io
import shutil
import subprocess
import sys
import tokenize
from pathlib import Path

TARGET = Path("s43.py")
TARGET_RUN_INDEX = 2
BACKUP = Path("s43.py.bak.rename_short_assets_20260602")
WATCH = {"_short", "_assets_detail"}

RUN_RENAMES = {
    "_short": "_run_short",
    "_assets_detail": "_run_assets_detail",
}

OVERVIEW_RENAMES = {
    "_short": "_overview_short",
    "_assets_detail": "_overview_assets_detail",
}

src = TARGET.read_text(encoding="utf-8", errors="surrogateescape")
lines = src.splitlines(keepends=True)
tree = ast.parse(src, filename=str(TARGET))

runs = [
    n for n in ast.walk(tree)
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "_run"
]
runs.sort(key=lambda n: (n.lineno, getattr(n, "end_lineno", n.lineno)))
if len(runs) < TARGET_RUN_INDEX:
    raise SystemExit(f"ERROR: cannot find _run #{TARGET_RUN_INDEX}")
run_node = runs[TARGET_RUN_INDEX - 1]

parent = {}
for node in ast.walk(tree):
    for child in ast.iter_child_nodes(node):
        parent[child] = node

func_nodes = [
    n for n in ast.walk(tree)
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
]

def inside(node, scope):
    return (
        getattr(scope, "lineno", 0) <= getattr(node, "lineno", -1)
        and getattr(node, "end_lineno", -1) <= getattr(scope, "end_lineno", -2)
    )

def direct_parent_func(node):
    cur = parent.get(node)
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur
        cur = parent.get(cur)
    return None

def containing_func(node):
    cur = node
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur
        cur = parent.get(cur)
    return None

def func_label(fn):
    return f"{fn.name}@{fn.lineno}-{getattr(fn, 'end_lineno', '?')}"

bindings = {fn: {} for fn in func_nodes}
for fn in func_nodes:
    p = direct_parent_func(fn)
    if p is not None:
        bindings.setdefault(p, {})[fn.name] = fn

target_bindings = {}

for old, new in RUN_RENAMES.items():
    bound = bindings.get(run_node, {}).get(old)
    if bound is None:
        raise SystemExit(f"ERROR: direct _run helper not found: {old}")
    target_bindings[(run_node, old)] = (bound, new)

overview_panels = [
    fn for fn in func_nodes
    if fn.name == "wallet_overview_panel" and inside(fn, run_node)
]
if not overview_panels:
    raise SystemExit("ERROR: no wallet_overview_panel found inside target _run")

for panel in overview_panels:
    for old, new in OVERVIEW_RENAMES.items():
        bound = bindings.get(panel, {}).get(old)
        if bound is not None:
            target_bindings[(panel, old)] = (bound, new)

if len(target_bindings) < 4:
    print("WARNING: fewer than four target bindings found.")
    for (scope, old), (bound, new) in target_bindings.items():
        print(f"  found {old} -> {new} in {func_label(scope)} bound at {func_label(bound)}")

def resolve_name(name, start_scope):
    scope = start_scope
    while scope is not None:
        if name in bindings.get(scope, {}):
            return scope, bindings[scope][name]
        scope = direct_parent_func(scope)
    return None, None

# Collect replacements:
# kind="def"  -> rename a function definition token on a line
# kind="name" -> rename a reference token near a source span
replacements = []

for (scope, old), (bound, new) in target_bindings.items():
    replacements.append({
        "kind": "def",
        "line": bound.lineno,
        "old": old,
        "new": new,
        "reason": f"def {old} in {func_label(scope)}",
    })

for node in ast.walk(run_node):
    if isinstance(node, ast.Name) and node.id in WATCH:
        scope = containing_func(node)
        binding_scope, bound = resolve_name(node.id, scope)
        if binding_scope is None:
            continue
        key = (binding_scope, node.id)
        if key in target_bindings:
            target_bound, new = target_bindings[key]
            if bound is target_bound:
                replacements.append({
                    "kind": "name",
                    "line": node.lineno,
                    "start_col": getattr(node, "col_offset", None),
                    "end_col": getattr(node, "end_col_offset", None),
                    "old": node.id,
                    "new": new,
                    "reason": f"name {node.id} resolved via {func_label(binding_scope)}",
                })

tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))

def token_key(tok):
    return (tok.start[0], tok.start[1])

def find_def_token(line_no, old):
    saw_def = False
    cands = []
    for tok in tokens:
        if tok.start[0] != line_no:
            continue
        if tok.type == tokenize.NAME and tok.string == "def":
            saw_def = True
            continue
        if saw_def and tok.type == tokenize.NAME and tok.string == old:
            cands.append(tok)
    if len(cands) != 1:
        raise SystemExit(
            f"ERROR: def token mapping ambiguous at line {line_no} for {old!r}: {len(cands)} candidate(s)"
        )
    return cands[0]

def find_name_token(line_no, old, start_col, end_col):
    cands = []
    for tok in tokens:
        if tok.start[0] != line_no:
            continue
        if tok.type == tokenize.NAME and tok.string == old:
            cands.append(tok)

    if not cands:
        raise SystemExit(f"ERROR: no NAME token {old!r} found on line {line_no}")

    # Prefer exact span containment.
    if start_col is not None and end_col is not None:
        exact = [
            tok for tok in cands
            if tok.start[1] >= start_col and tok.end[1] <= end_col
        ]
        if len(exact) == 1:
            return exact[0]

        cover = [
            tok for tok in cands
            if tok.start[1] <= start_col < tok.end[1]
        ]
        if len(cover) == 1:
            return cover[0]

        nearest = sorted(cands, key=lambda tok: abs(tok.start[1] - start_col))
        if len(nearest) >= 2 and abs(nearest[0].start[1] - start_col) == abs(nearest[1].start[1] - start_col):
            raise SystemExit(
                f"ERROR: ambiguous NAME token mapping at line {line_no} for {old!r}"
            )
        return nearest[0]

    if len(cands) != 1:
        raise SystemExit(
            f"ERROR: ambiguous NAME token mapping at line {line_no} for {old!r}: {len(cands)} candidate(s)"
        )
    return cands[0]

token_replacements = {}

for rep in replacements:
    if rep["kind"] == "def":
        tok = find_def_token(rep["line"], rep["old"])
    else:
        tok = find_name_token(
            rep["line"],
            rep["old"],
            rep.get("start_col"),
            rep.get("end_col"),
        )

    key = token_key(tok)
    prev = token_replacements.get(key)
    cur = (rep["old"], rep["new"], rep["reason"])
    if prev is not None and prev != cur:
        raise SystemExit(
            f"ERROR: conflicting replacement at {key}: {prev} vs {cur}"
        )
    token_replacements[key] = cur

new_tokens = []
applied = []

for tok in tokens:
    key = token_key(tok)
    if key in token_replacements:
        old, new, reason = token_replacements[key]
        if tok.string != old:
            raise SystemExit(
                f"ERROR: token mismatch at {tok.start}: expected {old!r}, got {tok.string!r}"
            )
        tok = tokenize.TokenInfo(tok.type, new, tok.start, tok.end, tok.line)
        applied.append((tok.start[0], tok.start[1], old, new, reason))
    new_tokens.append(tok)

new_src = tokenize.untokenize(new_tokens)
if new_src == src:
    raise SystemExit("ERROR: no changes produced")

if not BACKUP.exists():
    shutil.copy2(TARGET, BACKUP)
else:
    print(f"Backup already exists: {BACKUP}")

TARGET.write_text(new_src, encoding="utf-8", errors="surrogateescape")

compile_result = subprocess.run(
    [sys.executable, "-m", "py_compile", str(TARGET)],
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

if compile_result.returncode != 0:
    shutil.copy2(BACKUP, TARGET)
    print("ERROR: py_compile failed; restored backup.")
    print(compile_result.stderr)
    raise SystemExit(1)

print(f"OK: renamed {len(applied)} token(s)")
print(f"Backup: {BACKUP}")
print()
for line, col, old, new, reason in sorted(applied):
    print(f"  line {line}:{col}: {old} -> {new}    # {reason}")
print()
print("OK: py_compile passed")
