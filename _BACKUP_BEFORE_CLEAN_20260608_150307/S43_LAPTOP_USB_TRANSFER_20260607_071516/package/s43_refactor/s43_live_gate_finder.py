import ast
from pathlib import Path

FILE = "s43_dev_next.py"

GUARD_KEYWORDS = (
    "audit",
    "block",
    "guard",
    "halt",
    "lock",
)

TARGET_FUNCS = (
    "_s43_block_live_order_call",
    "_s43_block_live_order_call_async",
    "_audit_only_block",
    "_s43_audit_env_guard",
    "hard_blocks_all_orders",
)

EXCHANGE_TERMINALS = (
    "place_order",
    "cancel_order",
    "cancel_all_orders",
    "list_orders",
    "request",
)

src = Path(FILE).read_text(encoding="utf-8")
tree = ast.parse(src)

func_defs = {}
calls = []
assignments = []

def get_name(node):
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

class Visitor(ast.NodeVisitor):

    def visit_FunctionDef(self, node):
        func_defs[node.name] = node.lineno
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        func_defs[node.name] = node.lineno
        self.generic_visit(node)

    def visit_Call(self, node):
        name = get_name(node.func)
        if name:
            calls.append((name, node.lineno))
        self.generic_visit(node)

    def visit_Assign(self, node):
        value = get_name(node.value)

        for t in node.targets:
            target = get_name(t)
            if target and value:
                assignments.append((target, value, node.lineno))

        self.generic_visit(node)

Visitor().visit(tree)

print("===== GUARD FUNCTION DEFINITIONS =====")
for name in TARGET_FUNCS:
    if name in func_defs:
        print(f"{name}  -> line {func_defs[name]}")

print("\n===== GUARD CALL SITES =====")
for name, line in calls:
    for g in TARGET_FUNCS:
        if g in name:
            print(f"line {line} -> {name}")

print("\n===== POSSIBLE MONKEY PATCH / REBIND =====")
for target, value, line in assignments:

    if any(k in target.lower() for k in ("place_order","request","cancel","list")):
        if any(k in value.lower() for k in GUARD_KEYWORDS):
            print(f"line {line}")
            print("  target :", target)
            print("  value  :", value)

print("\n===== EXCHANGE TERMINAL CALL SITES =====")
for name, line in calls:

    for term in EXCHANGE_TERMINALS:
        if term in name.lower():

            print(f"line {line} -> {name}")

print("\n===== GUARD KEYWORD SCAN =====")
for name, line in calls:
    low = name.lower()

    if any(k in low for k in GUARD_KEYWORDS):
        print(f"line {line} -> {name}")

print("\n===== SUMMARY =====")
print("Total functions:", len(func_defs))
print("Total calls:", len(calls))
print("Total assignments:", len(assignments))
