import ast
from pathlib import Path

FILE = "s43_dev_next.py"

src = Path(FILE).read_text(encoding="utf-8")
tree = ast.parse(src)

functions = []
async_functions = []
classes = []

for node in ast.walk(tree):

    if isinstance(node, ast.FunctionDef):
        functions.append((node.name, node.lineno))

    if isinstance(node, ast.AsyncFunctionDef):
        async_functions.append((node.name, node.lineno))

    if isinstance(node, ast.ClassDef):
        classes.append((node.name, node.lineno))

print("\n===== CLASSES =====")
for name, line in sorted(classes, key=lambda x: x[1]):
    print(f"{line:5d}  {name}")

print("\n===== FUNCTIONS =====")
for name, line in sorted(functions, key=lambda x: x[1]):
    print(f"{line:5d}  {name}")

print("\n===== ASYNC FUNCTIONS =====")
for name, line in sorted(async_functions, key=lambda x: x[1]):
    print(f"{line:5d}  {name}")

print("\nSUMMARY")
print("classes:", len(classes))
print("functions:", len(functions))
print("async:", len(async_functions))
