from __future__ import annotations

import ast
import csv
import io
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path

TARGET = Path("s43.py")
OUT = Path("s43_persian_review.tsv")

PERSIAN_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")


@dataclass
class Item:
    kind: str
    line: int
    col: int
    end_line: int
    end_col: int
    text: str


def has_persian(s: str) -> bool:
    return bool(PERSIAN_RE.search(s or ""))


def one_line(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")


def scan_comments(source: str) -> list[Item]:
    out: list[Item] = []
    reader = io.StringIO(source).readline

    for tok in tokenize.generate_tokens(reader):
        if tok.type == tokenize.COMMENT and has_persian(tok.string):
            out.append(
                Item(
                    kind="comment",
                    line=tok.start[0],
                    col=tok.start[1],
                    end_line=tok.end[0],
                    end_col=tok.end[1],
                    text=tok.string,
                )
            )
    return out


def docstring_exprs(tree: ast.AST) -> list[ast.Expr]:
    out: list[ast.Expr] = []

    def check_body(body: list[ast.stmt]) -> None:
        if not body:
            return
        first = body[0]
        if isinstance(first, ast.Expr):
            value = first.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                out.append(first)

    if isinstance(tree, ast.Module):
        check_body(tree.body)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            check_body(node.body)

    return out


def scan_docstrings(tree: ast.AST) -> list[Item]:
    out: list[Item] = []

    for expr in docstring_exprs(tree):
        value = expr.value
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            continue

        if not has_persian(value.value):
            continue

        if not all(
            hasattr(expr, attr)
            for attr in ("lineno", "col_offset", "end_lineno", "end_col_offset")
        ):
            continue

        out.append(
            Item(
                kind="docstring",
                line=expr.lineno,
                col=expr.col_offset,
                end_line=expr.end_lineno,
                end_col=expr.end_col_offset,
                text=value.value,
            )
        )

    return out


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: {TARGET} not found")

    source = TARGET.read_text(encoding="utf-8")

    try:
        tree = ast.parse(source, filename=str(TARGET))
    except SyntaxError as exc:
        raise SystemExit(f"ERROR: AST parse failed: {exc}")

    items = scan_comments(source) + scan_docstrings(tree)
    items.sort(key=lambda x: (x.line, x.col, x.kind))

    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(
            [
                "id",
                "kind",
                "line",
                "col",
                "end_line",
                "end_col",
                "original",
                "replacement_english",
                "apply",
            ]
        )

        for i, item in enumerate(items, 1):
            writer.writerow(
                [
                    i,
                    item.kind,
                    item.line,
                    item.col,
                    item.end_line,
                    item.end_col,
                    one_line(item.text),
                    "",
                    "NO",
                ]
            )

    print("=" * 80)
    print("Persian comment/docstring extraction complete.")
    print(f"Target: {TARGET}")
    print(f"Output: {OUT}")
    print(f"Total review items: {len(items)}")
    print()
    print("Next step:")
    print(f"  Edit {OUT}")
    print("  Fill replacement_english")
    print("  Change apply from NO to YES only for safe items")
    print("=" * 80)


if __name__ == "__main__":
    main()
