#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "== S43 Deep Refactor Guard =="

TS=$(date +%Y%m%d_%H%M%S)

cat > s43_deep_refactor_guard.py <<'PY'
#!/usr/bin/env python3
import ast
import hashlib
import time
from pathlib import Path

ROOT = Path(".")
TARGET = Path("s43.py")
TS = time.strftime("%Y%m%d_%H%M%S")
REPORT = Path(f"s43_deep_refactor_report_{TS}.txt")

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "archive",
    "archive_packed_backup",
    "tools_archive",
    "release_backups",
}

def iter_py_files():
    for path in ROOT.rglob("*.py"):
        parts = set(path.parts)
        if parts & SKIP_DIRS:
            continue
        if path.name.startswith("s43_deep_refactor_guard"):
            continue
        yield path

def read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")

def module_suggestion(name):
    lowered = name.lower()
    groups = {
        "api": ("api", "route", "endpoint", "request", "response", "http", "server"),
        "auth": ("auth", "token", "login", "password", "session", "jwt"),
        "config": ("config", "setting", "env", "option"),
        "db": ("db", "database", "sql", "sqlite", "store", "repo"),
        "ui": ("ui", "menu", "screen", "render", "display", "panel"),
        "parser": ("parse", "parser", "regex", "extract", "tokenize"),
        "runtime": ("run", "start", "stop", "loop", "worker", "task"),
        "utils": ("util", "helper", "format", "normalize", "validate"),
    }
    for group, keys in groups.items():
        if any(k in lowered for k in keys):
            return group
    return "core"

def complexity_of_function(node):
    score = 1
    branch_nodes = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.ExceptHandler,
        ast.With,
        ast.AsyncWith,
        ast.IfExp,
        ast.BoolOp,
        ast.Match,
    )
    for child in ast.walk(node):
        if isinstance(child, branch_nodes):
            score += 1
    return score

def ast_fingerprint(node):
    clone = ast.parse(ast.unparse(node)).body[0]
    for child in ast.walk(clone):
        if hasattr(child, "lineno"):
            child.lineno = 0
        if hasattr(child, "col_offset"):
            child.col_offset = 0
        if hasattr(child, "end_lineno"):
            child.end_lineno = 0
        if hasattr(child, "end_col_offset"):
            child.end_col_offset = 0
    return hashlib.sha256(ast.dump(clone, include_attributes=False).encode()).hexdigest()

def line_hash_duplicates(path, text):
    blocks = {}
    lines = text.splitlines()
    window = 8
    for i in range(0, max(0, len(lines) - window + 1)):
        chunk_lines = [x.strip() for x in lines[i:i + window]]
        if not any(chunk_lines):
            continue
        chunk = "\n".join(chunk_lines)
        if len(chunk) < 120:
            continue
        h = hashlib.sha256(chunk.encode("utf-8", errors="ignore")).hexdigest()
        blocks.setdefault(h, []).append(i + 1)
    return [(path, positions) for positions in blocks.values() if len(positions) > 1]

def analyze_file(path):
    text = read_text(path)
    lines = text.splitlines()
    result = {
        "path": path,
        "line_count": len(lines),
        "functions": [],
        "classes": [],
        "complex": [],
        "module_groups": {},
        "duplicate_functions": [],
        "duplicate_blocks": [],
        "hotspots": [],
        "parse_error": None,
    }

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        result["parse_error"] = f"{exc.msg} line {exc.lineno}"
        return result

    fingerprints = {}

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno)
            length = max(1, end - node.lineno + 1)
            complexity = complexity_of_function(node)
            group = module_suggestion(node.name)
            info = {
                "name": node.name,
                "line": node.lineno,
                "end": end,
                "length": length,
                "complexity": complexity,
                "group": group,
            }
            result["functions"].append(info)
            result["module_groups"].setdefault(group, []).append(info)

            if length >= 120 or complexity >= 18:
                result["complex"].append(info)

            if complexity >= 25 or length >= 220:
                result["hotspots"].append(info)

            try:
                fp = ast_fingerprint(node)
                fingerprints.setdefault(fp, []).append(info)
            except Exception:
                pass

        elif isinstance(node, ast.ClassDef):
            end = getattr(node, "end_lineno", node.lineno)
            result["classes"].append({
                "name": node.name,
                "line": node.lineno,
                "end": end,
                "length": max(1, end - node.lineno + 1),
                "group": module_suggestion(node.name),
            })

    for items in fingerprints.values():
        if len(items) > 1:
            result["duplicate_functions"].append(items)

    result["duplicate_blocks"] = line_hash_duplicates(path, text)
    return result

def main():
    results = [analyze_file(path) for path in iter_py_files()]

    with REPORT.open("w", encoding="utf-8") as f:
        f.write("=== S43 DEEP REFACTOR REPORT ===\n")
        f.write(f"timestamp: {TS}\n\n")

        f.write("=== FILE SIZE SCAN ===\n")
        for r in sorted(results, key=lambda x: x["line_count"], reverse=True):
            if r["line_count"] >= 1000:
                f.write(f"{r['path']}: {r['line_count']} lines\n")

        f.write("\n=== PARSE ERRORS ===\n")
        any_parse = False
        for r in results:
            if r["parse_error"]:
                any_parse = True
                f.write(f"{r['path']}: {r['parse_error']}\n")
        if not any_parse:
            f.write("none\n")

        f.write("\n=== AUTO MODULE SPLIT SUGGESTIONS ===\n")
        target_results = [r for r in results if r["path"] == TARGET]
        if target_results:
            r = target_results[0]
            for group, funcs in sorted(r["module_groups"].items()):
                if len(funcs) >= 5:
                    first = min(x["line"] for x in funcs)
                    last = max(x["end"] for x in funcs)
                    f.write(f"s43_{group}.py: {len(funcs)} functions, approx lines {first}-{last}\n")
        else:
            f.write("s43.py not found\n")

        f.write("\n=== COMPLEX FUNCTIONS ===\n")
        found = False
        for r in results:
            for item in sorted(r["complex"], key=lambda x: (x["complexity"], x["length"]), reverse=True):
                found = True
                f.write(
                    f"{r['path']}:{item['line']} {item['name']} "
                    f"complexity={item['complexity']} length={item['length']} group={item['group']}\n"
                )
        if not found:
            f.write("none\n")

        f.write("\n=== PERFORMANCE HOTSPOTS ===\n")
        found = False
        for r in results:
            for item in sorted(r["hotspots"], key=lambda x: (x["complexity"], x["length"]), reverse=True):
                found = True
                f.write(
                    f"{r['path']}:{item['line']} {item['name']} "
                    f"complexity={item['complexity']} length={item['length']}\n"
                )
        if not found:
            f.write("none\n")

        f.write("\n=== DUPLICATE FUNCTIONS ===\n")
        found = False
        for r in results:
            for group in r["duplicate_functions"]:
                found = True
                names = ", ".join(f"{x['name']}@{x['line']}" for x in group)
                f.write(f"{r['path']}: {names}\n")
        if not found:
            f.write("none\n")

        f.write("\n=== DUPLICATE LINE BLOCKS ===\n")
        found = False
        for r in results:
            for path, positions in r["duplicate_blocks"][:50]:
                found = True
                pos = ", ".join(str(x) for x in positions[:10])
                f.write(f"{path}: repeated 8-line block at lines {pos}\n")
        if not found:
            f.write("none\n")

    print("DEEP REFACTOR SCAN COMPLETE")
    print("Report:", REPORT)

if __name__ == "__main__":
    main()
PY

chmod +x s43_deep_refactor_guard.py

python s43_deep_refactor_guard.py
python -m py_compile s43.py

echo "== DONE =="
echo "Run again:"
echo "python s43_deep_refactor_guard.py"
