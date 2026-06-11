import ast
from pathlib import Path
from collections import defaultdict

FILE = "s43_dev_next.py"

SIGNAL_KEYWORDS = (
    "signal",
    "entry",
    "strategy",
    "alpha",
    "decision"
)

EXECUTION_TERMINALS = (
    "place_order",
    "_place_order_impl",
    "place_limit",
    "place_market",
)

src = Path(FILE).read_text(encoding="utf-8")
tree = ast.parse(src)

func_stack = []
call_graph = defaultdict(set)

signal_funcs = set()
execution_funcs = set()

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
        name = node.name
        func_stack.append(name)

        for k in SIGNAL_KEYWORDS:
            if k in name.lower():
                signal_funcs.add(name)

        self.generic_visit(node)
        func_stack.pop()

    def visit_AsyncFunctionDef(self, node):
        name = node.name
        func_stack.append(name)

        for k in SIGNAL_KEYWORDS:
            if k in name.lower():
                signal_funcs.add(name)

        self.generic_visit(node)
        func_stack.pop()

    def visit_Call(self, node):

        name = get_name(node.func)

        if func_stack and name:
            caller = func_stack[-1]
            call_graph[caller].add(name)

            for e in EXECUTION_TERMINALS:
                if e in name.lower():
                    execution_funcs.add(caller)

        self.generic_visit(node)


Visitor().visit(tree)

print("===== SIGNAL RELATED FUNCTIONS =====")

for f in sorted(signal_funcs):
    print(f)

print("\n===== EXECUTION ENTRY FUNCTIONS =====")

for f in sorted(execution_funcs):
    print(f)

print("\n===== POSSIBLE SIGNAL → ORDER PATHS =====")

for s in signal_funcs:
    if s in call_graph:

        for callee in call_graph[s]:

            for e in EXECUTION_TERMINALS:

                if e in callee.lower():
                    print(f"{s}  ->  {callee}")

print("\n===== SUMMARY =====")

print("Signal functions:", len(signal_funcs))
print("Execution entry functions:", len(execution_funcs))
print("Call graph nodes:", len(call_graph))
