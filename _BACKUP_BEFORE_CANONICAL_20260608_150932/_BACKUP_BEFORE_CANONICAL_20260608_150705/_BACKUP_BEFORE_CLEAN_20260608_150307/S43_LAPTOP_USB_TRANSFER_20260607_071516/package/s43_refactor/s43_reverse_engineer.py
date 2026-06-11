import ast
from pathlib import Path

FILE="s43.py"

code=Path(FILE).read_text(errors="ignore")
tree=ast.parse(code)

func_lines={}
call_graph={}

class A(ast.NodeVisitor):
    def visit_FunctionDef(self,node):
        name=node.name
        func_lines[name]=node.lineno
        call_graph[name]=[]
        for n in ast.walk(node):
            if isinstance(n,ast.Call):
                if isinstance(n.func,ast.Name):
                    call_graph[name].append(n.func.id)
                elif isinstance(n.func,ast.Attribute):
                    call_graph[name].append(n.func.attr)
        self.generic_visit(node)

A().visit(tree)

keywords=("order","execute","submit","send")

targets=[f for f in func_lines if any(k in f.lower() for k in keywords)]

print("\nS43 ORDER EXECUTION MAP")
print("="*50)

for t in targets:
    print("\nFUNCTION:",t," line:",func_lines[t])
    for c in call_graph.get(t,[]):
        print("  ->",c)

print("\nNETWORK CALL INDICATORS")
print("="*50)

net=("post","get","request","ClientSession","fetch")

for f in call_graph:
    for c in call_graph[f]:
        if c in net:
            print(f,"->",c)

print("\nDONE")
