import ast
from pathlib import Path
from collections import defaultdict

FILE = "s43_dev_next.py"

TERMINALS = (
    "place_order",
    "cancel_order",
    "cancel_all_orders",
    "list_orders",
    "request",
)

src = Path(FILE).read_text(encoding="utf-8")
tree = ast.parse(src)

func_stack = []
call_graph = defaultdict(set)
terminal_hits = []

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
        func_stack.append(node.name)
        self.generic_visit(node)
        func_stack.pop()

    def visit_AsyncFunctionDef(self, node):
        func_stack.append(node.name)
        self.generic_visit(node)
        func_stack.pop()

    def visit_Call(self, node):

        name = get_name(node.func)

        if func_stack and name:
            caller = func_stack[-1]
            call_graph[caller].add(name)

            for t in TERMINALS:
                if t in name.lower():
                    terminal_hits.append(
                        (caller, name, node.lineno)
                    )

        self.generic_visit(node)

Visitor().visit(tree)

print("===== TERMINAL EXCHANGE CALLS =====")

for caller, callee, line in terminal_hits:
    print(f"line {line}")
    print("  caller :", caller)
    print("  callee :", callee)
    print()

print("===== FUNCTIONS TOUCHING EXCHANGE =====")

exchange_funcs = set()

for caller, callee, line in terminal_hits:
    exchange_funcs.add(caller)

for f in sorted(exchange_funcs):
    print(f)

print("\n===== CALL GRAPH (PARTIAL) =====")

for f in sorted(call_graph.keys()):

    for callee in call_graph[f]:

        for t in TERMINALS:
            if t in callee.lower():

                print(f"{f}  ->  {callee}")

print("\n===== SUMMARY =====")

print("Functions in call graph:", len(call_graph))
print("Exchange terminal hits:", len(terminal_hits))
print("Exchange touching functions:", len(exchange_funcs))
