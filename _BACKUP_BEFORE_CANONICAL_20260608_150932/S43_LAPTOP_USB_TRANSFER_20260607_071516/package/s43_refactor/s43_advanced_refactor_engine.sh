#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "== S43 ADVANCED REFACTOR ENGINE =="

if [ ! -f s43.py ]; then
echo "ERROR: s43.py not found"
exit 1
fi

ts=$(date +%Y%m%d_%H%M%S)

echo "[1] backup"
cp s43.py s43_backup_$ts.py

echo "[2] prepare project structure"

mkdir -p s43_project/core
mkdir -p s43_project/runtime
mkdir -p s43_project/api
mkdir -p s43_project/auth
mkdir -p s43_project/parser
mkdir -p s43_project/ui
mkdir -p s43_project/config
mkdir -p s43_project/reports

echo "[3] create analyzer"

cat << 'PY' > s43_project/refactor_engine.py
import ast
from pathlib import Path
from collections import defaultdict

SRC=Path("s43.py")
REPORT_DIR=Path("s43_project/reports")

source=SRC.read_text(encoding="utf-8")
tree=ast.parse(source)

functions=[]
classes=[]
imports=[]
large_functions=[]
call_map=defaultdict(set)

class CallVisitor(ast.NodeVisitor):
    def __init__(self,current):
        self.current=current
    def visit_Call(self,node):
        if isinstance(node.func,ast.Name):
            call_map[self.current].add(node.func.id)
        self.generic_visit(node)

for node in tree.body:

    if isinstance(node,ast.Import) or isinstance(node,ast.ImportFrom):
        imports.append(ast.unparse(node))

    if isinstance(node,ast.ClassDef):
        classes.append((node.name,node.lineno,node.end_lineno))

    if isinstance(node,ast.FunctionDef):

        length=node.end_lineno-node.lineno
        functions.append((node.name,node.lineno,node.end_lineno,length))

        if length>300:
            large_functions.append((node.name,length,node.lineno))

        visitor=CallVisitor(node.name)
        visitor.visit(node)

REPORT_DIR.mkdir(parents=True,exist_ok=True)

with open(REPORT_DIR/"functions_report.txt","w") as f:
    for name,start,end,length in functions:
        f.write(f"{name} {length} lines {start}-{end}\n")

with open(REPORT_DIR/"classes_report.txt","w") as f:
    for name,start,end in classes:
        f.write(f"{name} {start}-{end}\n")

with open(REPORT_DIR/"hotspots.txt","w") as f:
    for name,length,line in sorted(large_functions,key=lambda x:-x[1]):
        f.write(f"{name} {length} lines line:{line}\n")

with open(REPORT_DIR/"call_graph.txt","w") as f:
    for k,v in call_map.items():
        f.write(k+" -> "+",".join(v)+"\n")

print("functions:",len(functions))
print("classes:",len(classes))
print("hotspots:",len(large_functions))

print("reports written to:",REPORT_DIR)
PY

echo "[4] run analyzer"
python s43_project/refactor_engine.py

echo "[5] generate module placeholders"

touch s43_project/core/market.py
touch s43_project/core/orders.py
touch s43_project/core/wallet.py
touch s43_project/core/strategy.py
touch s43_project/core/snapshot.py

touch s43_project/runtime/engine.py
touch s43_project/runtime/watchdog.py

touch s43_project/api/api.py
touch s43_project/auth/auth.py
touch s43_project/parser/parser.py
touch s43_project/ui/panels.py
touch s43_project/config/config.py

echo "[6] syntax check"
python -m py_compile s43.py || true

echo "[7] summary"

echo "reports:"
ls s43_project/reports

echo ""
echo "ADVANCED ANALYSIS COMPLETE"
echo "backup: s43_backup_$ts.py"

