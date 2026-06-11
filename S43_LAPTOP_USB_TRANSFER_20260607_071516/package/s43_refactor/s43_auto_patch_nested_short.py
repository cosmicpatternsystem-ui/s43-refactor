from __future__ import annotations

import ast
import shutil
from pathlib import Path
from datetime import datetime

TARGET = Path("s43.py")

def die(msg: str):
    raise SystemExit(msg)

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def write_text(p: Path, s: str):
    p.write_text(s, encoding="utf-8")

def line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))

def nearest_block_header(lines: list[str], idx0: int, current_indent: int) -> str:
    """
    idx0: zero-based index of nested def line.
    Find nearest previous non-empty line with smaller indent, usually:
      if not s:
      except Exception:
    """
    for j in range(idx0 - 1, -1, -1):
        raw = lines[j]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        ind = line_indent(raw)
        if ind < current_indent:
            return stripped
    return ""

def find_nested_same_name_defs(src: str, target_name: str = "_short"):
    """
    Returns list of inner FunctionDef nodes where name == target_name
    and an ancestor FunctionDef also has the same name.
    """
    tree = ast.parse(src, filename=str(TARGET))
    found = []

    class V(ast.NodeVisitor):
        def __init__(self):
            self.stack = []

        def visit_FunctionDef(self, node: ast.FunctionDef):
            if node.name == target_name and any(a.name == target_name for a in self.stack):
                found.append(node)
            self.stack.append(node)
            self.generic_visit(node)
            self.stack.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            if node.name == target_name and any(a.name == target_name for a in self.stack):
                found.append(node)
            self.stack.append(node)
            self.generic_visit(node)
            self.stack.pop()

    V().visit(tree)
    return found

def replacement_for_context(header: str, indent: str) -> list[str]:
    h = header.strip()

    # حالت امن برای nested def داخل if not s:
    if h.startswith("if not s") or h.startswith("if not ") or h in {"if not s:", "if not s.strip():"}:
        return [indent + 'return "-"']

    # حالت امن برای nested def داخل except
    if h.startswith("except"):
        return [indent + "pass"]

    # fallback امن: بلاک را خالی نگذار
    return [indent + "pass"]

def main():
    if not TARGET.exists():
        die("ERROR: s43.py پیدا نشد. اسکریپت را کنار s43.py اجرا کن.")

    src = read_text(TARGET)

    # اول مطمئن شو فایل فعلی parse می‌شود
    try:
        ast.parse(src, filename=str(TARGET))
    except SyntaxError as e:
        die(f"ERROR: s43.py قبل از پچ SyntaxError دارد:\n{e}")

    nodes = find_nested_same_name_defs(src, "_short")

    if not nodes:
        print("OK: هیچ nested duplicate با نام def _short داخل def _short پیدا نشد.")
        print("No change.")
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_name(f"{TARGET.name}.bak_nested_short_{stamp}")
    shutil.copy2(TARGET, backup)
    print(f"Backup created: {backup}")

    lines = src.splitlines()

    # از پایین به بالا تا شماره خطوط تغییر نکند
    patches = []
    for n in nodes:
        if not hasattr(n, "end_lineno") or n.end_lineno is None:
            die("ERROR: Python فعلی end_lineno ندارد؛ با Python 3.8+ اجرا کن.")

        start0 = n.lineno - 1
        end0_exclusive = n.end_lineno

        def_line = lines[start0]
        indent_n = line_indent(def_line)
        indent = def_line[:indent_n]
        header = nearest_block_header(lines, start0, indent_n)
        repl = replacement_for_context(header, indent)

        patches.append((start0, end0_exclusive, repl, header, n.lineno, n.end_lineno))

    for start0, end0, repl, header, lineno, end_lineno in sorted(patches, reverse=True):
        old_preview = "\n".join(lines[start0:end0])
        print("=" * 70)
        print(f"Patch nested def _short at lines {lineno}-{end_lineno}")
        print(f"Nearest parent block header: {header!r}")
        print("Old:")
        print(old_preview)
        print("New:")
        print("\n".join(repl))
        lines[start0:end0] = repl

    new_src = "\n".join(lines) + ("\n" if src.endswith("\n") else "")

    # تست parse قبل از نوشتن نهایی
    try:
        ast.parse(new_src, filename=str(TARGET))
    except SyntaxError as e:
        restore = TARGET.with_name(f"{TARGET.name}.failed_patch_{stamp}")
        write_text(restore, new_src)
        die(
            "ERROR: نتیجه پچ SyntaxError دارد؛ فایل اصلی دست‌نخورده ماند.\n"
            f"Failed candidate saved as: {restore}\n"
            f"{e}"
        )

    write_text(TARGET, new_src)
    print("=" * 70)
    print("Patch written to s43.py")

    # compile check
    import py_compile
    try:
        py_compile.compile(str(TARGET), doraise=True)
    except Exception as e:
        shutil.copy2(backup, TARGET)
        die(
            "ERROR: compile بعد از پچ شکست خورد. بکاپ restore شد.\n"
            f"Restored from: {backup}\n"
            f"{e}"
        )

    print("OK: s43.py compile-clean است.")

    # گزارش نهایی watched names
    final_src = read_text(TARGET)
    final_nodes = find_nested_same_name_defs(final_src, "_short")
    print(f"Remaining nested def _short inside def _short: {len(final_nodes)}")

    for name in [
        "_short",
        "_assets_detail",
        "_run_short",
        "_overview_short",
        "_run_assets_detail",
        "_overview_assets_detail",
    ]:
        count = final_src.count(f"def {name}")
        print(f"def {name}: {count}")

    print("=" * 70)
    print("Done.")

if __name__ == "__main__":
    main()
