from __future__ import annotations

import ast
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field

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
    col: int
    qualname: str
    parent_qualname: str
    depth: int
    ancestor_names: tuple[str, ...] = field(default_factory=tuple)


def node_end_lineno(node: ast.AST) -> int | None:
    return getattr(node, "end_lineno", None)


def is_func(node: ast.AST) -> bool:
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))


class Audit(ast.NodeVisitor):
    def __init__(self):
        self.stack: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        self.funcs: list[FuncInfo] = []
        self.children_by_parent: dict[str, list[FuncInfo]] = defaultdict(list)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_func(node)

    def _visit_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        ancestor_names = tuple(n.name for n in self.stack)
        parent_qualname = ".".join(ancestor_names) if ancestor_names else "<module>"
        qualname = ".".join((*ancestor_names, node.name)) if ancestor_names else node.name

        info = FuncInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=node_end_lineno(node),
            col=node.col_offset,
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


def short_range(info: FuncInfo) -> str:
    if info.end_lineno:
        return f"{info.lineno}-{info.end_lineno}"
    return str(info.lineno)


def main():
    if not TARGET.exists():
        raise SystemExit(f"ERROR: {TARGET} not found")

    src = TARGET.read_text(encoding="utf-8")

    try:
        tree = ast.parse(src, filename=str(TARGET))
    except SyntaxError as e:
        raise SystemExit(
            "ERROR: s43.py is not parseable.\n"
            f"{e.__class__.__name__}: {e}"
        )

    audit = Audit()
    audit.visit(tree)

    funcs = audit.funcs

    print("=" * 80)
    print("S43 nested-def / shadowing audit")
    print("=" * 80)
    print(f"Target: {TARGET}")
    print(f"Total functions: {len(funcs)}")
    print()

    # 1) All nested defs
    nested = [f for f in funcs if f.depth > 0]
    print("=" * 80)
    print(f"1) Nested functions: {len(nested)}")
    print("=" * 80)
    if not nested:
        print("No nested functions found.")
    else:
        for f in nested:
            indent = "  " * min(f.depth, 6)
            print(
                f"{f.lineno:6d}: depth={f.depth:<2} "
                f"range={short_range(f):<13} "
                f"{indent}{f.name}  "
                f"parent={f.parent_qualname}"
            )
    print()

    # 2) Shadowing ancestor names
    shadow_ancestor = [
        f for f in funcs
        if f.depth > 0 and f.name in f.ancestor_names
    ]

    print("=" * 80)
    print(f"2) Ancestor-name shadowing: {len(shadow_ancestor)}")
    print("=" * 80)
    if not shadow_ancestor:
        print("No function shadows an ancestor function name.")
    else:
        for f in shadow_ancestor:
            ancestors = " > ".join(f.ancestor_names)
            print(
                f"{f.lineno:6d}: {f.name!r} shadows ancestor "
                f"in chain [{ancestors}] | qualname={f.qualname}"
            )
    print()

    # 3) Duplicate defs inside same parent scope
    duplicates = []
    for parent, children in audit.children_by_parent.items():
        by_name = defaultdict(list)
        for child in children:
            by_name[child.name].append(child)
        for name, same in by_name.items():
            if len(same) > 1:
                duplicates.append((parent, name, same))

    print("=" * 80)
    print(f"3) Duplicate function names in same parent scope: {len(duplicates)}")
    print("=" * 80)
    if not duplicates:
        print("No duplicate function names in the same parent scope.")
    else:
        for parent, name, same in duplicates:
            locs = ", ".join(f"{x.lineno}" for x in same)
            ranges = ", ".join(short_range(x) for x in same)
            print(
                f"parent={parent} | name={name!r} | "
                f"lines=[{locs}] | ranges=[{ranges}]"
            )
    print()

    # 4) Repeated function names anywhere in file
    by_global_name = defaultdict(list)
    for f in funcs:
        by_global_name[f.name].append(f)

    repeated_anywhere = {
        name: lst for name, lst in by_global_name.items()
        if len(lst) > 1
    }

    print("=" * 80)
    print(f"4) Repeated function names anywhere in file: {len(repeated_anywhere)}")
    print("=" * 80)
    if not repeated_anywhere:
        print("No repeated function names anywhere.")
    else:
        for name in sorted(repeated_anywhere):
            lst = repeated_anywhere[name]
            locs = ", ".join(f"{x.lineno}" for x in lst)
            parents = " | ".join(f"{x.lineno}:{x.parent_qualname}" for x in lst)
            print(f"{name!r}: count={len(lst)} lines=[{locs}] parents=[{parents}]")
    print()

    # 5) Watched names
    watched = [f for f in funcs if f.name in WATCH_NAMES]
    print("=" * 80)
    print(f"5) Watched helper names: {len(watched)}")
    print("=" * 80)
    if not watched:
        print("No watched helper names found.")
    else:
        for f in watched:
            print(
                f"{f.lineno:6d}: name={f.name:<28} "
                f"depth={f.depth:<2} range={short_range(f):<13} "
                f"parent={f.parent_qualname}"
            )
    print()

    # 6) Suspicious watched repeats
    watched_repeats = {
        name: lst for name, lst in by_global_name.items()
        if name in WATCH_NAMES and len(lst) > 1
    }

    print("=" * 80)
    print(f"6) Repeated watched names: {len(watched_repeats)}")
    print("=" * 80)
    if not watched_repeats:
        print("No repeated watched names.")
    else:
        for name in sorted(watched_repeats):
            lst = watched_repeats[name]
            print(f"{name!r}:")
            for f in lst:
                print(
                    f"  line={f.lineno:<6} depth={f.depth:<2} "
                    f"range={short_range(f):<13} parent={f.parent_qualname}"
                )
    print()

    print("=" * 80)
    print("Audit complete. No file was modified.")
    print("=" * 80)


if __name__ == "__main__":
    main()
