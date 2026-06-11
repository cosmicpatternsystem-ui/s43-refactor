import ast
from pathlib import Path

FILE = "s43_dev_next.py"
TARGETS = {
    "wallet_full_panel",
    "wallet_overview_panel",
    "phoenix_panel",
    "dzh_panel",
    "top8_panel",
    "top8_compact_panel",
    "render",
}

src = Path(FILE).read_text(encoding="utf-8")
tree = ast.parse(src)

class FuncAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.stack = []
        self.results = []

    def visit_ClassDef(self, node):
        self.stack.append(("class", node.name))
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node):
        self._visit_func(node, async_flag=False)

    def visit_AsyncFunctionDef(self, node):
        self._visit_func(node, async_flag=True)

    def _collect_assigned_names(self, node):
        assigned = set()
        params = set()

        for arg in getattr(node.args, "posonlyargs", []):
            params.add(arg.arg)
        for arg in node.args.args:
            params.add(arg.arg)
        for arg in node.args.kwonlyargs:
            params.add(arg.arg)
        if node.args.vararg:
            params.add(node.args.vararg.arg)
        if node.args.kwarg:
            params.add(node.args.kwarg.arg)

        class LocalVisitor(ast.NodeVisitor):
            def visit_Name(self, n):
                if isinstance(n.ctx, ast.Store):
                    assigned.add(n.id)
            def visit_FunctionDef(self, n):
                assigned.add(n.name)
            def visit_AsyncFunctionDef(self, n):
                assigned.add(n.name)
            def visit_ClassDef(self, n):
                assigned.add(n.name)

        LocalVisitor().visit(node)
        return params, assigned

    def _collect_used_names(self, node):
        used = set()
        class UseVisitor(ast.NodeVisitor):
            def visit_Name(self, n):
                if isinstance(n.ctx, ast.Load):
                    used.add(n.id)
        UseVisitor().visit(node)
        return used

    def _visit_func(self, node, async_flag=False):
        qprefix = ".".join(name for kind, name in self.stack)
        qname = f"{qprefix}.{node.name}" if qprefix else node.name

        if node.name in TARGETS:
            params, assigned = self._collect_assigned_names(node)
            used = self._collect_used_names(node)
            freevars = sorted(x for x in used if x not in params and x not in assigned and x not in dir(__builtins__))

            self.results.append({
                "name": node.name,
                "qname": qname,
                "lineno": node.lineno,
                "end": getattr(node, "end_lineno", None),
                "params": sorted(params),
                "assigned_count": len(assigned),
                "freevars": freevars,
                "scope": " > ".join(f"{kind}:{name}" for kind, name in self.stack) or "(top-level)",
            })

        self.stack.append(("async def" if async_flag else "def", node.name))
        self.generic_visit(node)
        self.stack.pop()

v = FuncAnalyzer()
v.visit(tree)

print("=== NESTED FREEVARS ===")
for r in sorted(v.results, key=lambda x: x["lineno"]):
    print(f'{r["qname"]} | line={r["lineno"]}-{r["end"]}')
    print(f'  scope: {r["scope"]}')
    print(f'  params: {r["params"]}')
    print(f'  assigned_count: {r["assigned_count"]}')
    print(f'  freevars({len(r["freevars"])}): {r["freevars"]}')
    print()
