import ast
from pathlib import Path
from collections import defaultdict

FILE = "s43_dev_next.py"

TARGET_KEYWORDS = (
    "order",
    "execute",
    "submit",
    "place",
    "cancel",
    "trade",
    "signal",
    "risk",
)

src = Path(FILE).read_text(encoding="utf-8")
tree = ast.parse(src)

func_nodes = {}
calls_map = defaultdict(set)
called_by_map = defaultdict(set)

def get_call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parts = []
        cur = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        parts.reverse()
        return ".".join(parts)
    return None

class FuncVisitor(ast.NodeVisitor):
    def __init__(self):
        self.current_func = None

    def visit_FunctionDef(self, node):
        prev = self.current_func
        self.current_func = node.name
        func_nodes[node.name] = node.lineno
        self.generic_visit(node)
        self.current_func = prev

    def visit_AsyncFunctionDef(self, node):
        prev = self.current_func
        self.current_func = node.name
        func_nodes[node.name] = node.lineno
        self.generic_visit(node)
        self.current_func = prev

    def visit_Call(self, node):
        if self.current_func:
            name = get_call_name(node.func)
            if name:
                calls_map[self.current_func].add(name)
                called_by_map[name].add(self.current_func)
        self.generic_visit(node)

FuncVisitor().visit(tree)

def interesting(name):
    low = name.lower()
    return any(k in low for k in TARGET_KEYWORDS)

targets = sorted([name for name in func_nodes if interesting(name)])

print("===== ORDER / EXECUTION RELATED FUNCTIONS =====")
for name in targets:
    print(f"{func_nodes[name]:5d}  {name}")

print("\n===== FORWARD CALL GRAPH =====")
for name in targets:
    print(f"\n--- {name} (line {func_nodes[name]}) ---")
    callees = sorted(calls_map.get(name, []))
    shown = False
    for callee in callees:
        if interesting(callee):
            print(f"  calls -> {callee}")
            shown = True
    if not shown:
        print("  calls -> [no keyword-matching callees]")

print("\n===== REVERSE CALL GRAPH =====")
for name in targets:
    print(f"\n--- {name} (line {func_nodes[name]}) ---")
    callers = sorted(called_by_map.get(name, []))
    shown = False
    for caller in callers:
        if interesting(caller):
            line = func_nodes.get(caller, "?")
            print(f"  called by <- {caller} (line {line})")
            shown = True
    if not shown:
        print("  called by <- [no keyword-matching callers]")

print("\n===== HIGH PRIORITY FOCUS =====")
focus_names = [
    "execute_order_v121",
    "place_order",
    "_place_order_impl",
    "_execute_trade",
    "place_limit",
    "place_market",
    "cancel_order",
    "cancel_all_orders",
]
for name in focus_names:
    if name in func_nodes:
        print(f"\n### {name} (line {func_nodes[name]})")
        print("  Forward:")
        for callee in sorted(calls_map.get(name, [])):
            print(f"    -> {callee}")
        print("  Reverse:")
        found = False
        for caller in sorted(called_by_map.get(name, [])):
            print(f"    <- {caller} (line {func_nodes.get(caller, '?')})")
            found = True
        if not found:
            print("    <- [none found]")
