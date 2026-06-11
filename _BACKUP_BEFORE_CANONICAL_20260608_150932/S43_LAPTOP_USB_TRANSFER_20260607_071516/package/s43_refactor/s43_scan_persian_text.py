from __future__ import annotations

import ast
import io
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path

TARGET = Path("s43.py")

# Arabic/Persian Unicode blocks
PERSIAN_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FFFB50-\uFDFFFE70-\uFEFF]")
NON_ASCII_IDENT_RE = re.compile(r"[^\x00-\x7F]")


@dataclass
class Hit:
    kind: str
    line: int
    col: int
    text: str


def has_persian(text: str) -> bool:
    return bool(PERSIAN_RE.search(text))


def shorten(text: str, width: int = 140) -> str:
    text = text.replace("\n", "\\n")
    if len(text) <= width:
        return text
    return text[: width - 3] + "..."


def scan_comments(source: str) -> list[Hit]:
    hits: list[Hit] = []
    reader = io.StringIO(source).readline
    for tok in tokenize.generate_tokens(reader):
        if tok.type == tokenize.COMMENT and has_persian(tok.string):
            hits.append(Hit("comment", tok.start[0], tok.start[1], tok.string))
    return hits


def get_docstring_nodes(tree: ast.AST) -> list[tuple[ast.AST, str, int, int]]:
    out: list[tuple[ast.AST, str, int, int]] = []

    def visit_body(owner: ast.AST, body: list[ast.stmt]) -> None:
        if not body:
            return
        first = body[0]
        if isinstance(first, ast.Expr):
            value = first.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                out.append((owner, value.value, first.lineno, first.col_offset))

    if isinstance(tree, ast.Module):
        visit_body(tree, tree.body)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            visit_body(node, node.body)

    return out


def scan_docstrings(tree: ast.AST) -> list[Hit]:
    hits: list[Hit] = []
    for owner, text, line, col in get_docstring_nodes(tree):
        if has_persian(text):
            owner_name = getattr(owner, "name", "<module>")
            hits.append(Hit(f"docstring:{type(owner).__name__}:{owner_name}", line, col, text))
    return hits


def scan_string_literals(tree: ast.AST) -> list[Hit]:
    hits: list[Hit] = []

    docstring_positions = set()
    for _, _, line, col in get_docstring_nodes(tree):
        docstring_positions.add((line, col))

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            line = getattr(node, "lineno", None)
            col = getattr(node, "col_offset", None)
            if line is None or col is None:
                continue
            if (line, col) in docstring_positions:
                continue
            if has_persian(node.value):
                hits.append(Hit("string", line, col, node.value))
    return hits


def scan_non_ascii_identifiers(tree: ast.AST) -> list[Hit]:
    hits: list[Hit] = []
    seen: set[tuple[str, int, int, str]] = set()

    for node in ast.walk(tree):
        for attr in ("name", "id", "arg", "attr"):
            value = getattr(node, attr, None)
            if isinstance(value, str) and NON_ASCII_IDENT_RE.search(value):
                line = getattr(node, "lineno", 0)
                col = getattr(node, "col_offset", 0)
                key = ("identifier", line, col, f"{attr}={value}")
                if key not in seen:
                    seen.add(key)
                    hits.append(Hit("identifier", line, col, f"{attr}={value}"))
    return hits


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: {TARGET} not found")

    source = TARGET.read_text(encoding="utf-8")

    try:
        tree = ast.parse(source, filename=str(TARGET))
    except SyntaxError as exc:
        raise SystemExit(f"ERROR: AST parse failed: {exc}")

    comments = scan_comments(source)
    docstrings = scan_docstrings(tree)
    strings = scan_string_literals(tree)
    identifiers = scan_non_ascii_identifiers(tree)

    all_hits = comments + docstrings + strings + identifiers
    all_hits.sort(key=lambda h: (h.line, h.col, h.kind))

    print("=" * 80)
    print("S43 PERSIAN TEXT SCAN")
    print("=" * 80)
    print(f"Target: {TARGET}")
    print(f"Total hits: {len(all_hits)}")
    print(f"Comments: {len(comments)}")
    print(f"Docstrings: {len(docstrings)}")
    print(f"Strings: {len(strings)}")
    print(f"Identifiers (non-ASCII): {len(identifiers)}")
    print()

    current_kind = None
    for hit in all_hits:
        if hit.kind != current_kind:
            current_kind = hit.kind
            print("-" * 80)
            print(current_kind.upper())
            print("-" * 80)
        print(f"line={hit.line:<6} col={hit.col:<4} text={shorten(hit.text)}")

    print()
    print("=" * 80)
    print("Read-only scan complete. No file was modified.")
    print("=" * 80)


if __name__ == "__main__":
    main()
