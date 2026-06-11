import ast
from pathlib import Path

FILE = "s43_dev_next.py"

TARGETS = {
    "phoenix_panel",
    "render",
    "dzh_panel",
    "snapshot",
    "_apply_resolved_fills",
    "wallet_overview_panel",
    "evaluate",
    "_update_market_snapshot_confidence",
    "_parse_depth",
    "_apply_one",
    "wallet_full_panel",
    "update",
    "top8_panel",
    "_run_raz_entry",
    "get_best_snapshot",
    "evaluate_entry",
    "top8_compact_panel",
    "_load_state",
    "__init__",
    "_phoenix_target_symbols",
}

src = Path(FILE).read_text(encoding="utf-8")
tree = ast.parse(src)

class ScopeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.stack = []
        self.matches = []

    def complexity_of(self, node):
        complexity = 1
        branches = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.BoolOp, ast.IfExp, ast.Match)):
                complexity += 1
                branches += 1
        length = (getattr(node, "end_lineno", None) or node.lineno) - node.lineno
        score = complexity * 2 + branches + length / 10
        return complexity, branches, length, score

    def visit_ClassDef(self, node):
        self.stack.append(("class", node.name))
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node):
        self._visit_func(node, async_flag=False)

    def visit_AsyncFunctionDef(self, node):
        self._visit_func(node, async_flag=True)

    def _visit_func(self, node, async_flag=False):
        qprefix = ".".join(name for kind, name in self.stack)
        qname = f"{qprefix}.{node.name}" if qprefix else node.name

        if node.name in TARGETS:
            complexity, branches, length, score = self.complexity_of(node)
            self.matches.append({
                "name": node.name,
                "qname": qname,
                "lineno": node.lineno,
                "end": getattr(node, "end_lineno", None),
                "length": length,
                "complexity": complexity,
                "branches": branches,
                "score": score,
                "async": async_flag,
                "scope_depth": len(self.stack),
                "scope": " > ".join(f"{kind}:{name}" for kind, name in self.stack) or "(top-level)",
            })

        self.stack.append(("async def" if async_flag else "def", node.name))
        self.generic_visit(node)
        self.stack.pop()

v = ScopeVisitor()
v.visit(tree)

print("=== TARGET LOCATIONS ===")
for m in sorted(v.matches, key=lambda x: (-x["score"], x["lineno"])):
    print(
        f'{m["qname"]} | line={m["lineno"]}-{m["end"]} '
        f'| score={round(m["score"],2)} '
        f'| complexity={m["complexity"]} '
        f'| branches={m["branches"]} '
        f'| lines={m["length"]} '
        f'| async={m["async"]} '
        f'| depth={m["scope_depth"]}'
    )
    print(f'  scope: {m["scope"]}')

print()
print("=== MISSING TARGETS ===")
found = {m["name"] for m in v.matches}
for name in sorted(TARGETS - found):
    print(name)
