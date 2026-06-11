from __future__ import annotations

import ast
import py_compile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

TARGET = Path("s43.py")

WATCH_NAMES = {
    "_short",
    "_assets_detail",
    "_run_short",
    "_overview_short",
    "_run_assets_detail",
    "_overview_assets_detail",
}


@dataclass
class FuncInfo:
    name: str
    lineno: int
    end_lineno: int | None
    col_offset: int
    qualname: str
    parent_qualname: str
    depth: int
    ancestor_names: tuple[str, ...] = field(default_factory=tuple)


def get_end_lineno(node: ast.AST) -> int | None:
    return getattr(node, "end_lineno", None)


class AuditVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.stack: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        self.funcs: list[FuncInfo] = []
        self.children_by_parent: dict[str, list[FuncInfo]] = defaultdict(list)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_func(node)

    def _visit_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        ancestor_names = tuple(n.name for n in self.stack)
        parent_qualname = ".".join(ancestor_names) if ancestor_names else "<module>"
        qualname = ".".join((*ancestor_names, node.name)) if ancestor_names else node.name

        info = FuncInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=get_end_lineno(node),
            col_offset=node.col_offset,
            qualname=qualname,
            parent_qualname=parent_qualname,
            depth=len(self.stack),
            ancestor_names=ancestor_names,
        )

        self.funcs.append(info)
        self.children_by_parent[parent_qualname].append(info)

        self.stack.append(node)
        self.generic_visit(node)
        self.stack.pop()


def format_range(info: FuncInfo) -> str:
    if info.end_lineno is not None:
        return f"{info.lineno}-{info.end_lineno}"
    return str(info.lineno)


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: {TARGET} not found")

    source = TARGET.read_text(encoding="utf-8")

    try:
        tree = ast.parse(source, filename=str(TARGET))
    except SyntaxError as exc:
        raise SystemExit(f"ERROR: AST parse failed for {TARGET}: {exc}")

    try:
        py_compile.compile(str(TARGET), doraise=True)
        compile_ok = True
        compile_error = None
    except Exception as exc:
        compile_ok = False
        compile_error = str(exc)

    visitor = AuditVisitor()
    visitor.visit(tree)

    funcs = visitor.funcs
    nested = [f for f in funcs if f.depth > 0]

    ancestor_shadowing = [
        f for f in funcs
        if f.depth > 0 and f.name in f.ancestor_names
    ]

    duplicates_same_scope: list[tuple[str, str, list[FuncInfo]]] = []
    for parent, children in visitor.children_by_parent.items():
        by_name: dict[str, list[FuncInfo]] = defaultdict(list)
        for child in children:
            by_name[child.name].append(child)
        for name, same in by_name.items():
            if len(same) > 1:
                duplicates_same_scope.append((parent, name, same))

    by_name_global: dict[str, list[FuncInfo]] = defaultdict(list)
    for f in funcs:
        by_name_global[f.name].append(f)

    repeated_watched = {
        name: items
        for name, items in by_name_global.items()
        if name in WATCH_NAMES and len(items) > 1
    }

    watched = [f for f in funcs if f.name in WATCH_NAMES]

    print("=" * 80)
    print("S43 FINAL AUDIT")
    print("=" * 80)
    print(f"Target: {TARGET}")
    print(f"Compile check: {'OK' if compile_ok else 'FAIL'}")
    if compile_error:
        print(f"Compile error: {compile_error}")
    print(f"Total functions: {len(funcs)}")
    print(f"Nested functions: {len(nested)}")
    print()

    print("=" * 80)
    print(f"1) Ancestor-name shadowing: {len(ancestor_shadowing)}")
    print("=" * 80)
    if not ancestor_shadowing:
        print("None")
    else:
        for f in ancestor_shadowing:
            chain = " > ".join(f.ancestor_names)
            print(
                f"line={f.lineno} name={f.name!r} "
                f"qualname={f.qualname} ancestors=[{chain}]"
            )
    print()

    print("=" * 80)
    print(f"2) Duplicate function names in same parent scope: {len(duplicates_same_scope)}")
    print("=" * 80)
    if not duplicates_same_scope:
        print("None")
    else:
        for parent, name, items in duplicates_same_scope:
            lines = ", ".join(str(x.lineno) for x in items)
            ranges = ", ".join(format_range(x) for x in items)
            print(f"parent={parent} name={name!r} lines=[{lines}] ranges=[{ranges}]")
    print()

    print("=" * 80)
    print(f"3) Watched helper names: {len(watched)}")
    print("=" * 80)
    if not watched:
        print("None")
    else:
        for f in watched:
            print(
                f"line={f.lineno:<6} "
                f"name={f.name:<24} "
                f"depth={f.depth:<2} "
                f"range={format_range(f):<12} "
                f"parent={f.parent_qualname}"
            )
    print()

    print("=" * 80)
    print(f"4) Repeated watched names: {len(repeated_watched)}")
    print("=" * 80)
    if not repeated_watched:
        print("None")
    else:
        for name in sorted(repeated_watched):
            print(f"name={name!r}")
            for f in repeated_watched[name]:
                print(
                    f"  line={f.lineno:<6} "
                    f"depth={f.depth:<2} "
                    f"range={format_range(f):<12} "
                    f"parent={f.parent_qualname}"
                )
    print()

    print("=" * 80)
    print("5) Summary")
    print("=" * 80)
    print(f"Compile OK: {compile_ok}")
    print(f"Ancestor shadowing count: {len(ancestor_shadowing)}")
    print(f"Same-scope duplicate count: {len(duplicates_same_scope)}")
    print(f"Repeated watched-name count: {len(repeated_watched)}")

    found_names = {f.name for f in watched}
    print(f"Watched names found: {', '.join(sorted(found_names)) if found_names else 'None'}")

    expected_present = [
        "_run_short",
        "_overview_short",
        "_run_assets_detail",
        "_overview_assets_detail",
    ]
    expected_absent = [
        "_short",
        "_assets_detail",
    ]

    print()
    print("Expected present:")
    for name in expected_present:
        print(f"  {name}: {'YES' if name in found_names else 'NO'}")

    print("Expected absent:")
    for name in expected_absent:
        print(f"  {name}: {'YES' if name not in found_names else 'NO'}")

    print()
    print("Read-only audit complete. No file was modified.")
    print("=" * 80)


if __name__ == "__main__":
    main()
