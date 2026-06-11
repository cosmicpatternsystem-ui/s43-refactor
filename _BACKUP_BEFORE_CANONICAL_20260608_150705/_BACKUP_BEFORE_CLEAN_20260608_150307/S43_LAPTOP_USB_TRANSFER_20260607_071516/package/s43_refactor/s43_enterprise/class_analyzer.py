import ast
from pathlib import Path
from collections import defaultdict

SRC = Path("s43.py")
REPORT = Path("s43_enterprise/reports")

source = SRC.read_text(encoding="utf-8")
tree = ast.parse(source)

classes=[]
methods=[]
large_methods=[]
call_map=defaultdict(set)

class MethodVisitor(ast.NodeVisitor):
    def __init__(self,cls,method):
        self.cls=cls
        self.method=method

    def visit_Call(self,node):
        if isinstance(node.func,ast.Attribute):
            name=node.func.attr
            call_map[f"{self.cls}.{self.method}"].add(name)

        if isinstance(node.func,ast.Name):
            call_map[f"{self.cls}.{self.method}"].add(node.func.id)

        self.generic_visit(node)

for node in tree.body:

    if isinstance(node,ast.ClassDef):

        classes.append((node.name,node.lineno,node.end_lineno))

        for item in node.body:

            if isinstance(item,ast.FunctionDef):

                length=item.end_lineno-item.lineno
                methods.append((node.name,item.name,length,item.lineno))

                if length>200:
                    large_methods.append((node.name,item.name,length,item.lineno))

                visitor=MethodVisitor(node.name,item.name)
                visitor.visit(item)

REPORT.mkdir(parents=True,exist_ok=True)

with open(REPORT/"classes.txt","w") as f:
    for c in classes:
        f.write(f"{c[0]} {c[1]}-{c[2]}\n")

with open(REPORT/"methods.txt","w") as f:
    for cls,m,l,line in methods:
        f.write(f"{cls}.{m} {l} lines line:{line}\n")

with open(REPORT/"large_methods.txt","w") as f:
    for cls,m,l,line in sorted(large_methods,key=lambda x:-x[2]):
        f.write(f"{cls}.{m} {l} lines line:{line}\n")

with open(REPORT/"method_calls.txt","w") as f:
    for k,v in call_map.items():
        f.write(k+" -> "+",".join(v)+"\n")

print("classes:",len(classes))
print("methods:",len(methods))
print("large_methods:",len(large_methods))
print("reports:",REPORT)
