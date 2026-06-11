#!/usr/bin/env python3
import ast
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

TARGET = Path("s43.py")
REPORT = Path("s43_ast_inventory_report.txt")
SYMBOLS = Path("s43_symbol_inventory.txt")

RISK_KEYWORDS = [
    "eval",
    "exec",
    "compile",
    "subprocess",
    "os.system",
    "pickle",
    "marshal",
    "pty",
    "shlex",
    "shell=True",
    "input(",
    "__import__",
    "importlib",
    "open(",
]

LARGE_CLASS_THRESHOLD = 200
LARGE_FUNC_THRESHOLD = 80
TOP_N = 20


def sha256_of_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_end_lineno(node):
    end = getattr(node, "end_lineno", None)
    if end is not None:
        return end
    last = getattr(node, "lineno", None)
    for child in ast.walk(node):
        child_end = getattr(child, "end_lineno", None)
        child_line = getattr(child, "lineno", None)
        if child_end is not None:
            last = max(last or child_end, child_end)
        elif child_line is not None:
            last = max(last or child_line, child_line)
    return last or getattr(node, "lineno", 0)


def span_of(node):
    start = getattr(node, "lineno", 0)
    end = get_end_lineno(node)
    return max(0, end - start + 1)


def import_entries(node):
    out = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            out.append(alias.name)
    elif isinstance(node, ast.ImportFrom):
        mod = node.module or ""
        for alias in node.names:
            out.append(f"{mod}:{alias.name}")
    return out


def method_count(cls):
    return sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in cls.body)


def classify_fn(node):
    if isinstance(node, ast.AsyncFunctionDef):
        return "async def"
    return "def"


def scan_risk_keywords(text: str):
    lines = text.splitlines()
    findings = defaultdict(list)
    for idx, line in enumerate(lines, start=1):
        for kw in RISK_KEYWORDS:
            if kw in line:
                findings[kw].append(idx)
    return findings


def main():
    if not TARGET.exists():
        raise SystemExit(f"Missing target: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(TARGET))

    classes = []
    functions = []
    imports = []
    top_names = defaultdict(list)

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            item = {
                "name": node.name,
                "line": node.lineno,
                "end": get_end_lineno(node),
                "span": span_of(node),
                "methods": method_count(node),
                "kind": "class",
            }
            classes.append(item)
            top_names[node.name].append(("class", node.lineno))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            item = {
                "name": node.name,
                "line": node.lineno,
                "end": get_end_lineno(node),
                "span": span_of(node),
                "kind": classify_fn(node),
            }
            functions.append(item)
            top_names[node.name].append(("function", node.lineno))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.extend(import_entries(node))

    dup_names = {k: v for k, v in top_names.items() if len(v) > 1}
    import_counter = Counter(imports)
    duplicate_imports = {k: c for k, c in import_counter.items() if c > 1}

    largest_classes = sorted(classes, key=lambda x: (-x["span"], x["line"]))[:TOP_N]
    largest_functions = sorted(functions, key=lambda x: (-x["span"], x["line"]))[:TOP_N]

    oversized_classes = [c for c in sorted(classes, key=lambda x: (-x["span"], x["line"])) if c["span"] >= LARGE_CLASS_THRESHOLD]
    oversized_functions = [f for f in sorted(functions, key=lambda x: (-x["span"], x["line"])) if f["span"] >= LARGE_FUNC_THRESHOLD]

    risk_findings = scan_risk_keywords(text)

    report_lines = []
    report_lines.append("AST INVENTORY REPORT")
    report_lines.append("====================")
    report_lines.append("")
    report_lines.append(f"Target: {TARGET}")
    report_lines.append(f"SHA256: {sha256_of_text(text)}")
    report_lines.append("")
    report_lines.append(f"Top-level classes: {len(classes)}")
    report_lines.append(f"Top-level functions: {len(functions)}")
    report_lines.append(f"Import entries: {len(imports)}")
    report_lines.append(f"Duplicate top-level names: {len(dup_names)}")
    report_lines.append(f"Duplicate imports: {len(duplicate_imports)}")
    report_lines.append("")

    report_lines.append("TOP LARGEST CLASSES")
    report_lines.append("-------------------")
    for c in largest_classes:
        report_lines.append(
            f'{c["name"]}: lines {c["line"]}-{c["end"]} | span={c["span"]} | methods={c["methods"]}'
        )
    report_lines.append("")

    report_lines.append("TOP LARGEST FUNCTIONS")
    report_lines.append("---------------------")
    for f in largest_functions:
        report_lines.append(
            f'{f["name"]}: {f["kind"]} | lines {f["line"]}-{f["end"]} | span={f["span"]}'
        )
    report_lines.append("")

    report_lines.append(f"OVERSIZED CLASSES (span >= {LARGE_CLASS_THRESHOLD})")
    report_lines.append("--------------------------------")
    for c in oversized_classes:
        report_lines.append(
            f'{c["name"]}: lines {c["line"]}-{c["end"]} | span={c["span"]} | methods={c["methods"]}'
        )
    report_lines.append("")

    report_lines.append(f"OVERSIZED FUNCTIONS (span >= {LARGE_FUNC_THRESHOLD})")
    report_lines.append("----------------------------------")
    for f in oversized_functions:
        report_lines.append(
            f'{f["name"]}: {f["kind"]} | lines {f["line"]}-{f["end"]} | span={f["span"]}'
        )
    report_lines.append("")

    report_lines.append("ALL CLASSES")
    report_lines.append("-----------")
    for c in classes:
        report_lines.append(
            f'{c["name"]}: lines {c["line"]}-{c["end"]} | span={c["span"]} | methods={c["methods"]}'
        )
    report_lines.append("")

    report_lines.append("ALL FUNCTIONS")
    report_lines.append("-------------")
    for f in functions:
        report_lines.append(
            f'{f["name"]}: {f["kind"]} | lines {f["line"]}-{f["end"]} | span={f["span"]}'
        )
    report_lines.append("")

    report_lines.append("IMPORTS")
    report_lines.append("-------")
    for imp in imports:
        report_lines.append(imp)
    report_lines.append("")

    report_lines.append("IMPORT DUPLICATES")
    report_lines.append("-----------------")
    if duplicate_imports:
        for name, count in sorted(duplicate_imports.items()):
            report_lines.append(f"{name}: count={count}")
    else:
        report_lines.append("(none)")
    report_lines.append("")

    report_lines.append("DUPLICATE TOP-LEVEL NAMES")
    report_lines.append("-------------------------")
    if dup_names:
        for name, occurrences in sorted(dup_names.items()):
            report_lines.append(f"{name}: {occurrences}")
    else:
        report_lines.append("(none)")
    report_lines.append("")

    report_lines.append("RISK KEYWORD SCAN")
    report_lines.append("-----------------")
    if risk_findings:
        for kw in RISK_KEYWORDS:
            if kw in risk_findings:
                lines = ", ".join(str(x) for x in risk_findings[kw][:50])
                extra = ""
                if len(risk_findings[kw]) > 50:
                    extra = f" ... total={len(risk_findings[kw])}"
                report_lines.append(f"{kw}: lines {lines}{extra}")
    else:
        report_lines.append("(none)")
    report_lines.append("")

    REPORT.write_text("\\n".join(report_lines) + "\\n", encoding="utf-8")

    symbol_lines = []
    symbol_lines.append("TOP-LEVEL SYMBOL INVENTORY")
    symbol_lines.append("==========================")
    symbol_lines.append("")
    for c in sorted(classes, key=lambda x: (x["name"].lower(), x["line"])):
        symbol_lines.append(f'{c["name"]}')
        symbol_lines.append(f'  - class @ line {c["line"]}')
    for f in sorted(functions, key=lambda x: (x["name"].lower(), x["line"])):
        symbol_lines.append(f'{f["name"]}')
        symbol_lines.append(f'  - function @ line {f["line"]}')
    SYMBOLS.write_text("\\n".join(symbol_lines) + "\\n", encoding="utf-8")

    print(f"Wrote: {REPORT}")
    print(f"Wrote: {SYMBOLS}")


if __name__ == "__main__":
    main()
