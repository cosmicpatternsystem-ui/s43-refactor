#!/usr/bin/env python3
import ast
import difflib
import pathlib
import sys
import time
from collections import defaultdict

SRC_PATH = pathlib.Path("s43.py").resolve()

OUT_CANDIDATE = pathlib.Path("s43_repair_candidate_output.py").resolve()
OUT_DIFF = pathlib.Path("s43_repair_candidate.diff").resolve()
OUT_REPORT = pathlib.Path("s43_repair_candidate_report.txt").resolve()

TARGET_METHODS = [
    "get_market_snapshot",
    "get_last_update_age",
    "get_all_market_stats",
    "get_trades",
    "get_balance",
    "conn_check",
    "place_order",
    "place_limit",
    "place_market",
    "cancel_all_orders",
    "list_orders",
    "cancel_order",
]

PREFERRED_BROKEN_OWNER_NAMES = {
    "_arzplus_market_snapshot",
    "_quantize_down",
}

BOUNDARY_CLASS = "ExchangeClient"

def println(buf, s=""):
    buf.append(str(s))

def read_source():
    if not SRC_PATH.exists():
        raise FileNotFoundError(f"not found: {SRC_PATH}")
    text = SRC_PATH.read_text(encoding="utf-8", errors="replace")
    return text, text.splitlines(keepends=True)

def build_parents(tree):
    parents = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents

def direct_owner(node, parents):
    p = parents.get(node)
    while p is not None:
        if isinstance(p, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            return p
        p = parents.get(p)
    return None

def owner_chain(node, parents):
    out = []
    p = parents.get(node)
    while p is not None:
        if isinstance(p, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(
                f"{type(p).__name__}:{p.name}@"
                f"{getattr(p, 'lineno', '?')}-{getattr(p, 'end_lineno', '?')}"
            )
        p = parents.get(p)
    return " <- ".join(out) if out else "<module>"

def line_indent_raw(line):
    s = line.rstrip("\n\r")
    return len(s) - len(s.lstrip(" "))

def dedent_block_to_class_method(block_lines):
    """
    The broken method usually starts at indent=4 because it is nested inside a top-level function.
    For direct ExchangeClient method, indent=4 is also correct.
    Therefore we generally keep method lines as-is.

    But if a block is accidentally indented deeper, normalize relative to its first non-empty line
    so method header becomes indent=4.
    """
    # Find first non-empty line
    first_indent = None
    for ln in block_lines:
        if ln.strip():
            first_indent = line_indent_raw(ln)
            break

    if first_indent is None:
        return block_lines

    target_indent = 4
    delta = first_indent - target_indent

    if delta == 0:
        return block_lines[:]

    out = []
    if delta > 0:
        # remove delta spaces if present
        for ln in block_lines:
            if ln.strip():
                if ln.startswith(" " * delta):
                    out.append(ln[delta:])
                else:
                    out.append(ln)
            else:
                out.append(ln)
    else:
        # add spaces
        add = " " * (-delta)
        for ln in block_lines:
            if ln.strip():
                out.append(add + ln)
            else:
                out.append(ln)
    return out

def make_quarantine_comment(block_lines, title):
    out = []
    out.append("\n")
    out.append("#" + "=" * 99 + "\n")
    out.append(f"# QUARANTINED BROKEN NESTED BLOCK: {title}\n")
    out.append("# This block was not removed in the candidate output.\n")
    out.append("# It is commented out to avoid duplicate/nested accidental definitions.\n")
    out.append("# Review manually before applying any final repair.\n")
    out.append("#" + "=" * 99 + "\n")
    for ln in block_lines:
        # Preserve blank lines as commented blanks for readability
        if ln.strip():
            out.append("# " + ln)
        else:
            out.append("#\n")
    out.append("#" + "=" * 99 + "\n")
    out.append("\n")
    return out

def collect_defs(tree):
    defs = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            defs.append(n)
    defs.sort(key=lambda x: (x.lineno, getattr(x, "end_lineno", x.lineno), x.name))
    return defs

def main():
    report = []
    println(report, "=" * 100)
    println(report, "S43 REPAIR CANDIDATE GENERATOR - OPTION A")
    println(report, "=" * 100)
    println(report, f"Source:       {SRC_PATH}")
    println(report, f"Candidate:    {OUT_CANDIDATE}")
    println(report, f"Diff:         {OUT_DIFF}")
    println(report, f"Report:       {OUT_REPORT}")
    println(report, "Mode:         READ-ONLY with respect to s43.py")
    println(report, f"Timestamp:    {time.strftime('%Y-%m-%d %H:%M:%S')}")
    println(report)

    try:
        src_text, lines = read_source()
    except Exception as e:
        println(report, f"ERROR reading source: {e}")
        OUT_REPORT.write_text("\n".join(report), encoding="utf-8")
        print("\n".join(report))
        return 1

    try:
        tree = ast.parse(src_text, filename=str(SRC_PATH))
    except SyntaxError as e:
        println(report, "SYNTAX ERROR: cannot generate candidate safely.")
        println(report, str(e))
        OUT_REPORT.write_text("\n".join(report), encoding="utf-8")
        print("\n".join(report))
        return 2

    parents = build_parents(tree)
    defs = collect_defs(tree)

    by_name = defaultdict(list)
    for n in defs:
        by_name[n.name].append(n)

    ex_nodes = [n for n in by_name.get(BOUNDARY_CLASS, []) if isinstance(n, ast.ClassDef)]
    if not ex_nodes:
        println(report, f"ERROR: {BOUNDARY_CLASS} class not found.")
        OUT_REPORT.write_text("\n".join(report), encoding="utf-8")
        print("\n".join(report))
        return 3

    exchange = ex_nodes[0]
    ex_start = exchange.lineno
    ex_end = exchange.end_lineno

    println(report, "1) EXCHANGECLIENT BOUNDARY")
    println(report, "-" * 100)
    println(report, f"ExchangeClient range: {ex_start}-{ex_end}")
    println(report)

    # Existing direct methods
    direct_methods = {}
    for n in defs:
        if n is exchange:
            continue
        if direct_owner(n, parents) is exchange:
            direct_methods.setdefault(n.name, []).append(n)

    println(report, "2) CURRENT DIRECT EXCHANGECLIENT MEMBERS")
    println(report, "-" * 100)
    for name in sorted(direct_methods):
        for n in direct_methods[name]:
            println(report, f"{n.lineno:5}-{n.end_lineno:5} {type(n).__name__:18} {name}")
    println(report)

    # Find candidate target methods not directly owned by ExchangeClient
    broken_candidates = []
    ok_methods = []
    missing_methods = []

    println(report, "3) TARGET METHOD OWNERSHIP")
    println(report, "-" * 100)

    for name in TARGET_METHODS:
        nodes = by_name.get(name, [])
        if not nodes:
            missing_methods.append(name)
            println(report, f"{name:28} MISSING")
            continue

        for n in nodes:
            owner = direct_owner(n, parents)
            owner_desc = "<module>" if owner is None else (
                f"{type(owner).__name__}:{owner.name}@{owner.lineno}-{owner.end_lineno}"
            )
            status = "OK" if owner is exchange else "BROKEN"
            println(
                report,
                f"{name:28} {status:8} {n.lineno:5}-{n.end_lineno:5} owner={owner_desc}"
            )
            if owner is exchange:
                ok_methods.append((name, n))
            else:
                broken_candidates.append((name, n, owner))

    println(report)

    # Choose canonical candidates:
    # Prefer methods under _arzplus_market_snapshot@2628-3557 style owner.
    # Avoid ExecutionEngine/mock methods unless no better option exists.
    selected = {}
    rejected = defaultdict(list)

    def score_candidate(name, node, owner):
        score = 0
        owner_name = getattr(owner, "name", None)

        if owner_name in PREFERRED_BROKEN_OWNER_NAMES:
            score += 1000

        # Prefer earlier corrupted region before MarketSpecsCache
        if 2400 <= node.lineno <= 3700:
            score += 500

        # Penalize mock/stress/fault/execution classes
        if owner_name in {"ExecutionEngine", "_MockExchangeForStress", "_FaultInjectExchange"}:
            score -= 1000

        # Prefer exact target function kind
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            score += 10

        # Stable preference: earlier line
        score -= node.lineno / 100000.0
        return score

    for name, node, owner in broken_candidates:
        sc = score_candidate(name, node, owner)
        item = (sc, name, node, owner)
        if name not in selected:
            selected[name] = item
        else:
            if sc > selected[name][0]:
                rejected[name].append(selected[name])
                selected[name] = item
            else:
                rejected[name].append(item)

    println(report, "4) SELECTED CANONICAL CANDIDATES FOR REINSERTION")
    println(report, "-" * 100)

    selected_items = []
    for name in TARGET_METHODS:
        if name in direct_methods:
            println(report, f"{name:28} SKIP already direct member of ExchangeClient")
            continue
        if name not in selected:
            println(report, f"{name:28} NO CANDIDATE FOUND")
            continue
        sc, _name, node, owner = selected[name]
        owner_desc = "<module>" if owner is None else f"{type(owner).__name__}:{owner.name}@{owner.lineno}-{owner.end_lineno}"
        println(
            report,
            f"{name:28} SELECT {node.lineno:5}-{node.end_lineno:5} owner={owner_desc} score={sc:.2f}"
        )
        selected_items.append((name, node, owner))

    println(report)

    if not selected_items:
        println(report, "No selected items. Candidate output will be identical to source.")
        candidate_lines = lines[:]
    else:
        # Prepare insertion block
        insertion = []
        insertion.append("\n")
        insertion.append("    " + "#" * 96 + "\n")
        insertion.append("    # REPAIR CANDIDATE INSERTION - REVIEW BEFORE APPLYING\n")
        insertion.append("    # These methods were extracted from accidental nested/top-level blocks.\n")
        insertion.append("    # Generated by s43_repair_candidate.py. Do not trust blindly.\n")
        insertion.append("    " + "#" * 96 + "\n")
        insertion.append("\n")

        for name, node, owner in selected_items:
            block = lines[node.lineno - 1 : node.end_lineno]
            block = dedent_block_to_class_method(block)
            insertion.append(f"    # ---- repaired candidate method: {name} from lines {node.lineno}-{node.end_lineno} ----\n")
            insertion.extend(block)
            if insertion and not insertion[-1].endswith("\n"):
                insertion[-1] += "\n"
            insertion.append("\n")

        insertion.append("    " + "#" * 96 + "\n")
        insertion.append("    # END REPAIR CANDIDATE INSERTION\n")
        insertion.append("    " + "#" * 96 + "\n")
        insertion.append("\n")

        # Insert just before ExchangeClient end.
        # Since ex_end is the last line inside the class body, insert before ex_end line if possible
        # to stay inside the class. But if ex_end points to a final return/pass line inside a method,
        # inserting there can corrupt a method.
        #
        # Safer heuristic: insert after the last direct member of ExchangeClient.
        # However AST says ExchangeClient ends at 2419. To keep candidate simple, insert at ex_end + 1
        # with 4-space indentation would NOT be inside class if the class actually ended.
        #
        # Therefore candidate output is not meant to be directly executed blindly. We create a separate
        # candidate file and diff for manual review.
        #
        # Better insertion anchor: before the first top-level def after ExchangeClient, i.e. line 2420.
        # This keeps the inserted 4-space methods visually as class continuation only if the prior class
        # structure permits it. In actual Python, if class ended due to dedent, this must replace the
        # offending top-level region or move class boundary manually.
        #
        # We still generate candidate by inserting before the first suspicious top-level helper after class.
        insert_at_1based = None
        suspicious_after = []
        for n in defs:
            if n.lineno > ex_end and n.name in {"_arzplus_last_trade_price", "_arzplus_market_snapshot", "_first_num", "_quantize_down"}:
                owner = direct_owner(n, parents)
                if owner is None:
                    suspicious_after.append(n)

        if suspicious_after:
            suspicious_after.sort(key=lambda n: n.lineno)
            insert_at_1based = suspicious_after[0].lineno
        else:
            insert_at_1based = ex_end + 1

        println(report, "5) INSERTION ANCHOR")
        println(report, "-" * 100)
        println(report, f"Candidate insertion line: before source line {insert_at_1based}")
        println(report, "NOTE: This is a candidate diff only. Review class boundary before applying.")
        println(report)

        candidate_lines = lines[:]
        idx = max(0, insert_at_1based - 1)
        candidate_lines[idx:idx] = insertion

        # Quarantine selected broken original blocks by commenting them out in candidate file.
        # Do from bottom to top to preserve indices.
        selected_ranges = []
        for name, node, owner in selected_items:
            selected_ranges.append((node.lineno, node.end_lineno, name, owner))

        # Merge exact selected ranges only, not whole owner function.
        selected_ranges.sort(reverse=True, key=lambda x: x[0])

        for start, end, name, owner in selected_ranges:
            # account for prior insertion if line after insertion anchor
            # Since we inserted before source line insert_at_1based, ranges after it shift by len(insertion).
            shift = len(insertion) if start >= insert_at_1based else 0
            a = start - 1 + shift
            b = end + shift
            if a < 0 or b > len(candidate_lines) or a >= b:
                continue
            original_block = candidate_lines[a:b]
            owner_desc = "<module>" if owner is None else f"{type(owner).__name__}:{owner.name}@{owner.lineno}-{owner.end_lineno}"
            quarantine = make_quarantine_comment(
                original_block,
                f"{name} original lines {start}-{end}, owner {owner_desc}"
            )
            candidate_lines[a:b] = quarantine

    candidate_text = "".join(candidate_lines)
    OUT_CANDIDATE.write_text(candidate_text, encoding="utf-8")

    diff = difflib.unified_diff(
        lines,
        candidate_lines,
        fromfile="s43.py",
        tofile="s43_repair_candidate_output.py",
        lineterm=""
    )
    diff_text = "\n".join(diff)
    OUT_DIFF.write_text(diff_text + ("\n" if diff_text else ""), encoding="utf-8")

    println(report, "6) OUTPUT FILES")
    println(report, "-" * 100)
    println(report, f"Wrote candidate: {OUT_CANDIDATE}")
    println(report, f"Wrote diff:      {OUT_DIFF}")
    println(report, f"Wrote report:    {OUT_REPORT}")
    println(report)

    println(report, "7) REVIEW COMMANDS")
    println(report, "-" * 100)
    println(report, "Inspect selected candidates:")
    println(report, "  grep -nE \"SELECT|SKIP|NO CANDIDATE|BROKEN|INSERTION\" s43_repair_candidate_report.txt")
    println(report)
    println(report, "Inspect diff summary:")
    println(report, "  grep -nE \"^@@|REPAIR CANDIDATE|QUARANTINED|async def|get_market_snapshot|place_order|place_limit\" s43_repair_candidate.diff | head -200")
    println(report)
    println(report, "Syntax-check candidate only:")
    println(report, "  python -m py_compile s43_repair_candidate_output.py")
    println(report)
    println(report, "IMPORTANT:")
    println(report, "  This script did NOT modify s43.py.")
    println(report, "  Candidate output is for review before Option B.")
    println(report)

    println(report, "DONE")

    OUT_REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
