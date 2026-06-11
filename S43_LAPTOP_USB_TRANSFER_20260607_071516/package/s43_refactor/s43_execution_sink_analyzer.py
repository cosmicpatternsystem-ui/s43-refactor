import ast
from pathlib import Path
from collections import defaultdict, deque

FILE = "s43_dev_next.py"

SINK_KEYWORDS = (
    "place_order",
    "api_client.request",
    "self.request",
)

src = Path(FILE).read_text(encoding="utf-8")
tree = ast.parse(src)

call_graph = defaultdict(set)
reverse_graph = defaultdict(set)
func_stack = []

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
            reverse_graph[name].add(caller)

        self.generic_visit(node)


Visitor().visit(tree)

sinks = []

for caller, callees in call_graph.items():
    for callee in callees:
        for s in SINK_KEYWORDS:
            if s in callee:
                sinks.append((caller, callee))


print("===== EXECUTION SINKS FOUND =====")

for c, s in sinks:
    print(f"{c}  ->  {s}")


print("\n===== TRACE BACK PATHS =====")

def trace_back(start):

    visited = set()
    q = deque([(start, [start])])

    paths = []

    while q:
        node, path = q.popleft()

        if node not in reverse_graph:
            paths.append(path)
            continue

        for parent in reverse_graph[node]:

            if parent not in visited:
                visited.add(parent)
                q.append((parent, [parent] + path))

    return paths


for caller, sink in sinks:

    paths = trace_back(caller)

    for p in paths[:5]:
        print(" -> ".join(p + [sink]))

print("\n===== SUMMARY =====")
print("Functions in call graph:", len(call_graph))
print("Execution sinks:", len(sinks))
