#!/usr/bin/env python3
import ast
import io
import re
import tokenize
import py_compile
from pathlib import Path
from collections import defaultdict

TARGET = Path("s43.py")
PERSIAN_RE = re.compile(r"[\u0600-\u06FF]")

EXPECTED_HELPERS = {
    "_run_short",
    "_run_assets_detail",
    "_overview_short",
    "_overview_assets_detail",
}

OLD_HELPERS = {
    "_short",
    "_assets_detail",
}

print("=" * 80)
print("S43 ROADMAP FINAL AUDIT")
print("Target:", TARGET)
print("=" * 80)

if not TARGET.exists():
    raise SystemExit("ERROR: s43.py not found")

source = TARGET.read_text(encoding="utf-8")

print("\n[1] Compile check")
try:
    py_compile.compile(str(TARGET), doraise=True)
    print("Compile check: OK")
except Exception as e:
    print("Compile check: FAIL")
    print(e)
    raise SystemExit(1)

print("\n[2] AST parse")
try:
    tree = ast.parse(source, filename=str(TARGET))
    print("AST parse: OK")
except SyntaxError as e:
    print("AST parse: FAIL")
    print(e)
    raise SystemExit(1)

defs = defaultdict(list)
class DefVisitor(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        defs[node.name].append(node.lineno)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        defs[node.name].append(node.lineno)
        self.generic_visit(node)

DefVisitor().visit(tree)

print("\n[3] Expected renamed helpers")
missing = []
for name in sorted(EXPECTED_HELPERS):
    locs = defs.get(name, [])
    if locs:
        print(f"OK: {name} -> lines {locs}")
    else:
        print(f"MISSING: {name}")
        missing.append(name)

print("\n[4] Old helper names")
old_found = []
for name in sorted(OLD_HELPERS):
    locs = defs.get(name, [])
    if locs:
        print(f"FOUND OLD NAME: {name} -> lines {locs}")
        old_found.append(name)
    else:
        print(f"OK: {name} not present as function def")

print("\n[5] Duplicate function names")
duplicates = {name: locs for name, locs in defs.items() if len(locs) > 1}
watched_duplicates = {
    name: locs for name, locs in duplicates.items()
    if name in EXPECTED_HELPERS or name in OLD_HELPERS
}
if watched_duplicates:
    for name, locs in sorted(watched_duplicates.items()):
        print(f"WATCHED DUPLICATE: {name} -> lines {locs}")
else:
    print("No watched duplicate helper definitions found.")

print("\n[6] Persian in comments/docstrings")
persian_hits = []

reader = io.StringIO(source).readline
for tok in tokenize.generate_tokens(reader):
    tok_type, tok_text, start, end, line = tok
    if tok_type == tokenize.COMMENT and PERSIAN_RE.search(tok_text):
        persian_hits.append(("comment", start[0], tok_text.strip()))

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
        doc = ast.get_docstring(node, clean=False)
        if doc and PERSIAN_RE.search(doc):
            line = getattr(node, "lineno", 1)
            persian_hits.append(("docstring", line, doc.strip().splitlines()[0]))

if persian_hits:
    for kind, line, text in persian_hits:
        print(f"PERSIAN {kind}: line {line}: {text}")
else:
    print("No Persian comments/docstrings found.")

print("\n[7] Summary")
failed = False

if missing:
    print("FAIL: Missing expected helpers:", ", ".join(sorted(missing)))
    failed = True

if old_found:
    print("FAIL: Old helper names still present:", ", ".join(sorted(old_found)))
    failed = True

if watched_duplicates:
    print("FAIL: Watched duplicate helper definitions found.")
    failed = True

if persian_hits:
    print("FAIL: Persian comments/docstrings still present.")
    failed = True

if failed:
    print("\nROADMAP AUDIT: FAIL")
    raise SystemExit(1)

print("ROADMAP AUDIT: OK")
