import ast
from pathlib import Path
from collections import defaultdict

CORE = Path("s43_project/core")
OUT = Path("s43_project/architecture")

OUT.mkdir(exist_ok=True)

class_deps = defaultdict(set)
method_calls = defaultdict(set)

files = list(CORE.glob("*.py"))

for file in files:

    if file.name == "__init__.py":
        continue

    source = file.read_text(encoding="utf-8")

    try:
        tree = ast.parse(source)
    except:
        continue

    for node in ast.walk(tree):

        if isinstance(node, ast.ClassDef):

            current_class = node.name

            for item in node.body:

                if isinstance(item, ast.FunctionDef):

                    method = f"{current_class}.{item.name}"

                    for sub in ast.walk(item):

                        if isinstance(sub, ast.Call):

                            if isinstance(sub.func, ast.Attribute):
                                method_calls[method].add(sub.func.attr)

                            if isinstance(sub.func, ast.Name):
                                method_calls[method].add(sub.func.id)

                        if isinstance(sub, ast.Name):
                            class_deps[current_class].add(sub.id)

with open(OUT/"class_dependencies.txt","w") as f:
    for cls,deps in class_deps.items():
        f.write(cls+" -> "+",".join(sorted(deps))+"\n")

with open(OUT/"method_call_graph.txt","w") as f:
    for m,calls in method_calls.items():
        f.write(m+" -> "+",".join(sorted(calls))+"\n")

print("classes analyzed:",len(class_deps))
print("methods analyzed:",len(method_calls))
print("reports:",OUT)

