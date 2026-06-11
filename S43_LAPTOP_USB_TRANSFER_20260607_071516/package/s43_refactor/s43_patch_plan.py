#!/usr/bin/env python3
import ast
import pathlib
import sys
from collections import defaultdict

PATH = pathlib.Path("s43.py").resolve()

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

TOP_LEVEL_HELPERS = [
    "_arzplus_last_trade_price",
    "_arzplus_market_snapshot",
    "_first_num",
    "_quantize_down",
]

BOUNDARY_NAMES = [
    "ExchangeClient",
    "MarketSpecsCache",
    "ExecutionEngine",
]

def read_source():
    if not PATH.exists():
        print(f"ERROR: file not found: {PATH}")
        sys.exit(1)
    src = PATH.read_text(encoding="utf-8", errors="replace")
    return src, src.splitlines()

def build_parents(tree):
    parents = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents

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

def direct_owner(node, parents):
    p = parents.get(node)
    while p is not None:
        if isinstance(p, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            return p
        p = parents.get(p)
    return None

def node_kind(node):
    return type(node).__name__

def line_indent(line):
    return len(line) - len(line.lstrip(" "))

def print_header(title):
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)

def print_sub(title):
    print()
    print("-" * 100)
    print(title)
    print("-" * 100)

def main():
    src, lines = read_source()

    print_header("S43 STRUCTURAL PATCH PLAN - DIAGNOSTIC ONLY")
    print(f"FILE: {PATH}")
    print("MODE: read-only / no file modification")

    try:
        tree = ast.parse(src, filename=str(PATH))
    except SyntaxError as e:
        print("SYNTAX ERROR:")
        print(e)
        sys.exit(2)

    parents = build_parents(tree)

    all_defs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            all_defs.append(node)

    all_defs.sort(key=lambda n: (n.lineno, getattr(n, "end_lineno", n.lineno)))

    by_name = defaultdict(list)
    for n in all_defs:
        by_name[n.name].append(n)

    # ------------------------------------------------------------------------------------
    # 1) Critical boundaries
    # ------------------------------------------------------------------------------------
    print_header("1) CRITICAL STRUCTURE BOUNDARIES")

    for name in BOUNDARY_NAMES:
        nodes = by_name.get(name, [])
        if not nodes:
            print(f"{name:24} NOT FOUND")
            continue
        for n in nodes:
            print(
                f"{name:24} {node_kind(n):16} "
                f"{n.lineno:5}-{getattr(n, 'end_lineno', '?'):5} "
                f"owner: {owner_chain(n, parents)}"
            )

    # ------------------------------------------------------------------------------------
    # 2) ExchangeClient actual body
    # ------------------------------------------------------------------------------------
    print_header("2) EXCHANGECLIENT BODY RANGE")

    ex_nodes = by_name.get("ExchangeClient", [])
    if not ex_nodes:
        print("ERROR: ExchangeClient not found.")
        sys.exit(3)

    ex = ex_nodes[0]
    ex_start = ex.lineno
    ex_end = getattr(ex, "end_lineno", None)

    print(f"ExchangeClient range: {ex_start}-{ex_end}")

    print_sub("Direct members of ExchangeClient")
    direct_members = []
    for n in all_defs:
        if n is ex:
            continue
        if direct_owner(n, parents) is ex:
            direct_members.append(n)

    if not direct_members:
        print("No direct function/class members found inside ExchangeClient.")
    else:
        for n in direct_members:
            print(
                f"{n.lineno:5}-{getattr(n, 'end_lineno', '?'):5} "
                f"{node_kind(n):16} {n.name}"
            )

    # ------------------------------------------------------------------------------------
    # 3) Target method ownership
    # ------------------------------------------------------------------------------------
    print_header("3) TARGET METHOD OWNERSHIP")

    broken = []
    ok = []
    missing = []

    for name in TARGET_METHODS:
        nodes = by_name.get(name, [])
        if not nodes:
            missing.append(name)
            print(f"{name:28} NOT FOUND")
            continue

        for n in nodes:
            owner = direct_owner(n, parents)
            owner_desc = "<module>" if owner is None else f"{node_kind(owner)}:{owner.name}@{owner.lineno}-{getattr(owner, 'end_lineno', '?')}"
            status = "OK" if owner is ex else "BROKEN"
            if owner is ex:
                ok.append((name, n))
            else:
                broken.append((name, n, owner))
            print(
                f"{name:28} {status:7} "
                f"{n.lineno:5}-{getattr(n, 'end_lineno', '?'):5} "
                f"owner: {owner_desc}"
            )

    # ------------------------------------------------------------------------------------
    # 4) Suspicious top-level helpers / corrupted regions
    # ------------------------------------------------------------------------------------
    print_header("4) SUSPICIOUS TOP-LEVEL / NESTING REGIONS")

    for name in TOP_LEVEL_HELPERS:
        nodes = by_name.get(name, [])
        if not nodes:
            print(f"{name:32} NOT FOUND")
            continue
        for n in nodes:
            owner = direct_owner(n, parents)
            owner_desc = "<module>" if owner is None else f"{node_kind(owner)}:{owner.name}@{owner.lineno}-{getattr(owner, 'end_lineno', '?')}"
            indent = line_indent(lines[n.lineno - 1]) if 1 <= n.lineno <= len(lines) else "?"
            print(
                f"{name:32} {node_kind(n):16} "
                f"{n.lineno:5}-{getattr(n, 'end_lineno', '?'):5} "
                f"indent={indent!s:3} owner: {owner_desc}"
            )

    # ------------------------------------------------------------------------------------
    # 5) Broken nested method groups
    # ------------------------------------------------------------------------------------
    print_header("5) BROKEN NESTED METHOD GROUPS")

    groups = defaultdict(list)
    for name, n, owner in broken:
        if owner is None:
            key = "<module>"
        else:
            key = f"{node_kind(owner)}:{owner.name}@{owner.lineno}-{getattr(owner, 'end_lineno', '?')}"
        groups[key].append((name, n))

    if not groups:
        print("No broken target methods detected.")
    else:
        for key, arr in groups.items():
            print_sub(f"Owner: {key}")
            for name, n in sorted(arr, key=lambda x: x[1].lineno):
                indent = line_indent(lines[n.lineno - 1]) if 1 <= n.lineno <= len(lines) else "?"
                print(
                    f"{n.lineno:5}-{getattr(n, 'end_lineno', '?'):5} "
                    f"indent={indent:<3} {node_kind(n):16} {name}"
                )

    # ------------------------------------------------------------------------------------
    # 6) Raw snippets around broken starts
    # ------------------------------------------------------------------------------------
    print_header("6) RAW SNIPPETS AROUND BROKEN TARGET METHODS")

    seen_ranges = set()
    for name, n, owner in sorted(broken, key=lambda x: x[1].lineno):
        a = max(1, n.lineno - 3)
        b = min(len(lines), n.lineno + 6)
        key = (a, b)
        if key in seen_ranges:
            continue
        seen_ranges.add(key)

        print_sub(f"{name} around lines {a}-{b}")
        for i in range(a, b + 1):
            line = lines[i - 1]
            print(f"{i:5} ind={line_indent(line):<3} | {repr(line)}")

    # ------------------------------------------------------------------------------------
    # 7) Proposed repair plan
    # ------------------------------------------------------------------------------------
    print_header("7) PROPOSED REPAIR PLAN - NO CHANGES APPLIED")

    print("Current diagnosis:")
    if broken:
        print("  BROKEN: some critical methods are not direct members of ExchangeClient.")
    else:
        print("  OK: all found target methods are direct members of ExchangeClient.")

    if missing:
        print()
        print("Missing target method names:")
        for x in missing:
            print(f"  - {x}")

    print()
    print("Recommended repair strategy:")
    print("  1. Do NOT patch Phase4/gate logic yet.")
    print("  2. First repair class structure and indentation.")
    print("  3. Move/reinsert canonical target methods as direct members of ExchangeClient.")
    print("  4. Remove or quarantine accidental nested duplicate blocks.")
    print("  5. Re-run runtime introspection and require exists=True for all critical methods.")
    print("  6. Only after that, test Phase4 enforcement paths.")

    print()
    print("Candidate methods that should become direct ExchangeClient methods:")
    for name in TARGET_METHODS:
        print(f"  - {name}")

    print()
    print("Important detected ranges:")
    print(f"  ExchangeClient current range: {ex_start}-{ex_end}")

    for key, arr in groups.items():
        print(f"  Broken group under {key}:")
        for name, n in sorted(arr, key=lambda x: x[1].lineno):
            print(f"    - {name}: {n.lineno}-{getattr(n, 'end_lineno', '?')}")

    print()
    print("Suggested next command after manual/auto repair:")
    print("  python s43_patch_plan.py")
    print()
    print("DONE: diagnostic patch plan generated. s43.py was not modified.")

if __name__ == "__main__":
    main()
