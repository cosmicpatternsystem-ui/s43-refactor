import ast
from pathlib import Path

FILE = "s43_dev_next.py"

src = Path(FILE).read_text(encoding="utf-8")
tree = ast.parse(src)

classes = {}
top_level_functions = []
panel_functions = []
interesting = {
    "snapshot": [],
    "evaluate": [],
    "fill": [],
    "render": [],
    "depth": [],
    "wallet": [],
    "phoenix": [],
}

for node in tree.body:
    if isinstance(node, ast.ClassDef):
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)
                lname = item.name.lower()
                if "panel" in lname or "render" in lname:
                    panel_functions.append((node.name, item.name, item.lineno))
                for key in interesting:
                    if key in lname:
                        interesting[key].append((node.name, item.name, item.lineno))
        classes[node.name] = methods

    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        top_level_functions.append((node.name, node.lineno))
        lname = node.name.lower()
        if "panel" in lname or "render" in lname:
            panel_functions.append(("(top-level)", node.name, node.lineno))
        for key in interesting:
            if key in lname:
                interesting[key].append(("(top-level)", node.name, node.lineno))

print("=== PARSE OK ===")
print("Top-level functions:", len(top_level_functions))
print("Classes:", len(classes))
print()

print("=== TOP 20 CLASSES BY METHOD COUNT ===")
ranked = sorted(classes.items(), key=lambda kv: len(kv[1]), reverse=True)[:20]
for cls, methods in ranked:
    print(f"{cls}: {len(methods)} methods")
print()

print("=== PANEL/RENDER CANDIDATES ===")
for owner, name, lineno in sorted(panel_functions, key=lambda x: x[2])[:120]:
    print(f"{lineno}: {owner}.{name}")
print()

print("=== INTERESTING FUNCTIONS ===")
for key, items in interesting.items():
    print(f"[{key}]")
    for owner, name, lineno in sorted(items, key=lambda x: x[2])[:80]:
        print(f"  {lineno}: {owner}.{name}")
    print()

print("=== TRADINGBOTOPS METHODS ===")
for cls_name in classes:
    if cls_name == "TradingBotOps":
        for name in classes[cls_name]:
            print(name)
