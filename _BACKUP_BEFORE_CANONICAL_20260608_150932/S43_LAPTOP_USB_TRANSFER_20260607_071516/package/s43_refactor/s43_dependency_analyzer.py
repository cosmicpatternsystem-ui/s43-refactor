import ast
from pathlib import Path
from collections import defaultdict, Counter

FILE = "s43_dev_next.py"

src = Path(FILE).read_text(encoding="utf-8")
tree = ast.parse(src)

call_graph = defaultdict(set)
reverse_graph = defaultdict(set)
class_methods = defaultdict(set)

current_class = None
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

    def visit_ClassDef(self, node):
        global current_class
        prev = current_class
        current_class = node.name
        self.generic_visit(node)
        current_class = prev

    def visit_FunctionDef(self, node):
        name = node.name
        if current_class:
            class_methods[current_class].add(name)
        func_stack.append(name)
        self.generic_visit(node)
        func_stack.pop()

    def visit_AsyncFunctionDef(self, node):
        name = node.name
        if current_class:
            class_methods[current_class].add(name)
        func_stack.append(name)
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

fan_out = {k: len(v) for k, v in call_graph.items()}
fan_in = {k: len(v) for k, v in reverse_graph.items()}

top_fan_out = sorted(fan_out.items(), key=lambda x: x[1], reverse=True)[:15]
top_fan_in = sorted(fan_in.items(), key=lambda x: x[1], reverse=True)[:15]

print("===== TOP 15 FAN-OUT (Most Calling Functions) =====")
for name, count in top_fan_out:
    print(f"{name}: {count}")

print("\n===== TOP 15 FAN-IN (Most Called Functions) =====")
for name, count in top_fan_in:
    print(f"{name}: {count}")

print("\n===== CLASS METHOD COUNTS =====")
class_sizes = {cls: len(methods) for cls, methods in class_methods.items()}
for cls, count in sorted(class_sizes.items(), key=lambda x: x[1], reverse=True)[:15]:
    print(f"{cls}: {count}")

print("\n===== SUMMARY =====")
print("Total functions:", len(call_graph))
print("Total classes:", len(class_methods))
