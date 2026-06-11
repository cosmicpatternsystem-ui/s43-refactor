#!/usr/bin/env python3
import ast
import time
from pathlib import Path

TARGET = Path("s43.py")
TS = time.strftime("%Y%m%d_%H%M%S")
REPORT = Path(f"s43_deep_refactor_fast_report_{TS}.txt")

def complexity(node):
    score = 1
    checks = (
        ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try,
        ast.ExceptHandler, ast.BoolOp, ast.IfExp, ast.With, ast.AsyncWith
    )
    for child in ast.walk(node):
        if isinstance(child, checks):
            score += 1
    return score

def group_name(name):
    n = name.lower()
    if any(x in n for x in ("api", "route", "endpoint", "http", "request", "response")):
        return "api"
    if any(x in n for x in ("auth", "token", "login", "session", "jwt", "password")):
        return "auth"
    if any(x in n for x in ("config", "setting", "env", "option")):
        return "config"
    if any(x in n for x in ("db", "sql", "sqlite", "store", "repo", "database")):
        return "db"
    if any(x in n for x in ("parse", "regex", "extract", "token")):
        return "parser"
    if any(x in n for x in ("run", "start", "stop", "loop", "worker", "task")):
        return "runtime"
    if any(x in n for x in ("ui", "menu", "render", "display", "screen")):
        return "ui"
    return "core"

if not TARGET.exists():
    raise SystemExit("ERROR: s43.py not found")

text = TARGET.read_text(encoding="utf-8", errors="replace")
lines = text.splitlines()

tree = ast.parse(text)

functions = []
classes = []
groups = {}

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        end = getattr(node, "end_lineno", node.lineno)
        length = max(1, end - node.lineno + 1)
        c = complexity(node)
        g = group_name(node.name)
        item = (node.name, node.lineno, end, length, c, g)
        functions.append(item)
        groups.setdefault(g, []).append(item)

    elif isinstance(node, ast.ClassDef):
        end = getattr(node, "end_lineno", node.lineno)
        classes.append((node.name, node.lineno, end, max(1, end - node.lineno + 1), group_name(node.name)))

names = {}
duplicates = []

for name, line, end, length, c, g in functions:
    if name in names:
        duplicates.append((name, names[name], line))
    else:
        names[name] = line

with REPORT.open("w", encoding="utf-8") as f:
    f.write("=== S43 FAST DEEP REFACTOR REPORT ===\n")
    f.write(f"timestamp: {TS}\n")
    f.write(f"file: s43.py\n")
    f.write(f"total_lines: {len(lines)}\n")
    f.write(f"functions: {len(functions)}\n")
    f.write(f"classes: {len(classes)}\n\n")

    f.write("=== MODULE SPLIT SUGGESTIONS ===\n")
    for g, items in sorted(groups.items()):
        if len(items) >= 5:
            first = min(x[1] for x in items)
            last = max(x[2] for x in items)
            f.write(f"s43_{g}.py: {len(items)} functions, approx lines {first}-{last}\n")

    f.write("\n=== COMPLEX FUNCTIONS ===\n")
    complex_items = [x for x in functions if x[3] >= 120 or x[4] >= 18]
    for name, line, end, length, c, g in sorted(complex_items, key=lambda x: (x[4], x[3]), reverse=True):
        f.write(f"s43.py:{line} {name} complexity={c} length={length} group={g}\n")
    if not complex_items:
        f.write("none\n")

    f.write("\n=== PERFORMANCE HOTSPOTS ===\n")
    hot = [x for x in functions if x[3] >= 220 or x[4] >= 25]
    for name, line, end, length, c, g in sorted(hot, key=lambda x: (x[4], x[3]), reverse=True):
        f.write(f"s43.py:{line} {name} complexity={c} length={length} group={g}\n")
    if not hot:
        f.write("none\n")

    f.write("\n=== DUPLICATE FUNCTION NAMES ===\n")
    for name, first, second in duplicates:
        f.write(f"{name}: first line {first}, duplicate line {second}\n")
    if not duplicates:
        f.write("none\n")

print("FAST DEEP REFACTOR SCAN COMPLETE")
print("Report:", REPORT)
