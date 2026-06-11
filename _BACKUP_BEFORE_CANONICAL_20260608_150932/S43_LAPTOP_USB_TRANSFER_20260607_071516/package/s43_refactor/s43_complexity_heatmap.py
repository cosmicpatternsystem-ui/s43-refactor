import ast
from pathlib import Path

FILE = "s43_dev_next.py"

src = Path(FILE).read_text(encoding="utf-8")
tree = ast.parse(src)

functions = []

class ComplexityVisitor(ast.NodeVisitor):

    def visit_FunctionDef(self, node):

        complexity = 1
        branches = 0

        for child in ast.walk(node):

            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.BoolOp)):
                complexity += 1
                branches += 1

        length = node.end_lineno - node.lineno if node.end_lineno else 0

        score = complexity * 2 + branches + length / 10

        functions.append({
            "name": node.name,
            "complexity": complexity,
            "branches": branches,
            "length": length,
            "score": score
        })

        self.generic_visit(node)


ComplexityVisitor().visit(tree)

top = sorted(functions, key=lambda x: x["score"], reverse=True)[:20]

print("===== TOP 20 COMPLEX FUNCTIONS =====")

for f in top:

    print(
        f'{f["name"]} | score={round(f["score"],2)} '
        f'| complexity={f["complexity"]} '
        f'| branches={f["branches"]} '
        f'| lines={f["length"]}'
    )

print("\n===== SUMMARY =====")

print("Total functions analyzed:", len(functions))

