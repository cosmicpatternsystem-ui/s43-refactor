#!/usr/bin/env python3
import re
import ast
import shutil
import time
from pathlib import Path

TARGET = Path("s43.py")
TS = int(time.time())
REPORT = Path(f"phase53_auto_audit_report_{TS}.txt")
SNIP_DIR = Path(f"phase53_snippets_{TS}")

KEY_PATTERNS = [
    r"\bTemporaryPause\b",
    r"\bpause_sec\b",
    r"\be\.pause_sec\b",
    r"\bpenalize\s*\(",
    r"\basyncio\.sleep\s*\(",
    r"\bsleep\s*\(",
    r"\brecord_failure\s*\(",
    r"\brecord_success\s*\(",
    r"\bshould_retry\s*\(",
    r"\bAdaptiveRetryHandler\b",
    r"\bSmartCircuitBreaker\b",
    r"\b_record_failure_if_transient\b",
    r"\bplace_order\b",
    r"\bplace_limit\b",
    r"\b_execute_trade\b",
    r"\b_place\b",
]

TARGET_NAMES = {
    "classes": [
        "AdaptiveRetryHandler",
        "SmartCircuitBreaker",
        "TemporaryPause",
    ],
    "functions": [
        "penalize",
        "_record_failure_if_transient",
        "place_order",
        "place_limit",
        "_place",
        "_execute_trade",
    ]
}

def backup_file(path: Path):
    backup = path.with_name(f"{path.stem}_before_phase53_audit_{TS}{path.suffix}")
    shutil.copy2(path, backup)
    return backup

def read_lines(path: Path):
    return path.read_text(encoding="utf-8", errors="replace").splitlines()

def safe_slice(lines, start, end):
    start = max(1, start)
    end = min(len(lines), end)
    return "\n".join(f"{i:05d}: {lines[i-1]}" for i in range(start, end + 1))

def extract_defs_with_ast(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text)
    lines = text.splitlines()
    found = []

    class Visitor(ast.NodeVisitor):
        def visit_ClassDef(self, node):
            found.append(("class", node.name, node.lineno, getattr(node, "end_lineno", node.lineno)))
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            found.append(("def", node.name, node.lineno, getattr(node, "end_lineno", node.lineno)))
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            found.append(("async def", node.name, node.lineno, getattr(node, "end_lineno", node.lineno)))
            self.generic_visit(node)

    Visitor().visit(tree)
    return found, lines

def grep_patterns(lines, patterns):
    results = []
    for idx, line in enumerate(lines, start=1):
        for pat in patterns:
            if re.search(pat, line):
                results.append((idx, pat, line))
    return results

def write_report(report_path: Path, content: str):
    report_path.write_text(content, encoding="utf-8")

def main():
    if not TARGET.exists():
        print("ERROR: s43.py not found in current directory")
        raise SystemExit(1)

    SNIP_DIR.mkdir(parents=True, exist_ok=True)

    backup = backup_file(TARGET)
    defs, lines = extract_defs_with_ast(TARGET)
    grep_hits = grep_patterns(lines, KEY_PATTERNS)

    selected_defs = []
    for kind, name, start, end in defs:
        if name in TARGET_NAMES["classes"] or name in TARGET_NAMES["functions"]:
            selected_defs.append((kind, name, start, end))

    out = []
    out.append("# Phase 5.3 Automated Audit Report")
    out.append(f"timestamp: {TS}")
    out.append(f"target: {TARGET}")
    out.append(f"backup: {backup}")
    out.append("")

    out.append("## 1. Selected Definitions")
    if selected_defs:
        for kind, name, start, end in sorted(selected_defs, key=lambda x: x[2]):
            out.append(f"- {kind} {name}: lines {start}-{end}")
    else:
        out.append("- No target definitions found")
    out.append("")

    out.append("## 2. Pattern Hits")
    if grep_hits:
        for lineno, pat, line in grep_hits:
            out.append(f"[line {lineno}] pattern={pat} :: {line}")
    else:
        out.append("- No pattern hits found")
    out.append("")

    out.append("## 3. Extracted Definitions")
    if selected_defs:
        for kind, name, start, end in sorted(selected_defs, key=lambda x: x[2]):
            out.append("")
            out.append(f"### {kind} {name} ({start}-{end})")
            snippet = safe_slice(lines, start, end)
            out.append(snippet)

            snip_file = SNIP_DIR / f"{start:05d}_{name}.txt"
            snip_file.write_text(snippet, encoding="utf-8")
    else:
        out.append("- Nothing extracted")
    out.append("")

    out.append("## 4. Context Windows Around Critical Hits")
    critical_tokens = [
        "TemporaryPause",
        "pause_sec",
        "penalize(",
        "asyncio.sleep(",
        "_record_failure_if_transient",
        "should_retry(",
        "record_failure(",
        "record_success(",
    ]
    seen = set()
    for idx, line in enumerate(lines, start=1):
        if any(tok in line for tok in critical_tokens):
            key = (idx, line)
            if key in seen:
                continue
            seen.add(key)
            out.append("")
            out.append(f"### Context around line {idx}")
            out.append(safe_slice(lines, idx - 5, idx + 12))

    write_report(REPORT, "\n".join(out))
    print(f"[OK] report: {REPORT}")
    print(f"[OK] snippets dir: {SNIP_DIR}")
    print(f"[OK] backup: {backup}")

if __name__ == "__main__":
    main()
