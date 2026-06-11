import ast
import builtins
from pathlib import Path

FILE = "s43_dev_next.py"

CLASS_NAME = "WallStreetDashboardManager"
RUN_NAME = "_run"

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

BUILTINS = set(dir(builtins))

def arg_names(args):
    out = set()
    for a in getattr(args, "posonlyargs", []):
        out.add(a.arg)
    for a in args.args:
        out.add(a.arg)
    for a in args.kwonlyargs:
        out.add(a.arg)
    if args.vararg:
        out.add(args.vararg.arg)
    if args.kwarg:
        out.add(args.kwarg.arg)
    return out

class LocalAndUseCollector(ast.NodeVisitor):
    """
    Collect local definitions and used names inside one function body.
    Important: does NOT descend into nested functions/classes/lambdas.
    """
    def __init__(self):
        self.loads = set()
        self.stores = set()
        self.globals = set()
        self.nonlocals = set()

    def visit_Global(self, node):
        self.globals.update(node.names)

    def visit_Nonlocal(self, node):
        self.nonlocals.update(node.names)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.loads.add(node.id)
        elif isinstance(node.ctx, (ast.Store, ast.Del)):
            self.stores.add(node.id)

    def visit_FunctionDef(self, node):
        # nested function name is local, but its body is a separate scope
        self.stores.add(node.name)

    def visit_AsyncFunctionDef(self, node):
        self.stores.add(node.name)

    def visit_ClassDef(self, node):
        # class name is local, body is a separate scope
        self.stores.add(node.name)

    def visit_Lambda(self, node):
        # separate scope
        return

    def visit_ExceptHandler(self, node):
        if node.name:
            self.stores.add(node.name)
        self.generic_visit(node)

def collect_func_scope(fn):
    c = LocalAndUseCollector()
    locals0 = set(arg_names(fn.args))
    for stmt in fn.body:
        c.visit(stmt)
    locals0 |= c.stores
    # global declarations are not local
    locals0 -= c.globals
    free = set(c.loads) - locals0 - BUILTINS
    return {
        "params": sorted(arg_names(fn.args)),
        "locals": sorted(locals0),
        "loads": sorted(c.loads),
        "free": sorted(free),
        "globals_decl": sorted(c.globals),
        "nonlocals_decl": sorted(c.nonlocals),
    }

def find_class(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and n.name == name:
            return n
    return None

def find_direct_method(cls, name):
    for n in cls.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None

def direct_nested_functions(fn):
    out = {}
    for stmt in fn.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[stmt.name] = stmt
    return out

def module_defs(tree):
    defs = set()
    imports = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                for x in ast.walk(t):
                    if isinstance(x, ast.Name):
                        defs.add(x.id)
        elif isinstance(n, ast.AnnAssign):
            t = n.target
            if isinstance(t, ast.Name):
                defs.add(t.id)
        elif isinstance(n, ast.Import):
            for a in n.names:
                imports.add((a.asname or a.name.split(".")[0]))
        elif isinstance(n, ast.ImportFrom):
            for a in n.names:
                imports.add(a.asname or a.name)
    return defs | imports

cls = find_class(tree, CLASS_NAME)
if not cls:
    raise SystemExit(f"Class not found: {CLASS_NAME}")

run = find_direct_method(cls, RUN_NAME)
if not run:
    raise SystemExit(f"Method not found: {CLASS_NAME}.{RUN_NAME}")

run_scope = collect_func_scope(run)
run_locals = set(run_scope["locals"])
mod_defs = module_defs(tree)

nested = direct_nested_functions(run)

print("=== RUN SCOPE SUMMARY ===")
print(f"{CLASS_NAME}.{RUN_NAME} | line={run.lineno}-{getattr(run, 'end_lineno', None)}")
print(f"run_params: {run_scope['params']}")
print(f"run_locals_count: {len(run_scope['locals'])}")
print(f"direct_nested_funcs: {sorted(nested.keys())}")
print()

print("=== DASHBOARD CLOSURE DEPS ===")
for name in sorted(TARGETS, key=lambda x: getattr(nested.get(x), "lineno", 10**9)):
    fn = nested.get(name)
    if not fn:
        print(f"{name}: NOT FOUND as direct nested function")
        continue

    sc = collect_func_scope(fn)
    free = set(sc["free"])

    # True closure deps from _run locals.
    closure_from_run = sorted(free & run_locals)

    # Sibling nested functions used by this function.
    sibling_calls = sorted(free & set(nested.keys()))

    # Probably module/global deps. These do not need to be parameters if kept in same module.
    module_or_import = sorted((free & mod_defs) - set(nested.keys()))

    # Unknown names may be globals dynamically created or analyzer limitations.
    unknown = sorted(free - set(closure_from_run) - set(sibling_calls) - set(module_or_import))

    print(f"{CLASS_NAME}.{RUN_NAME}.{name} | line={fn.lineno}-{getattr(fn, 'end_lineno', None)}")
    print(f"  params: {sc['params']}")
    print(f"  locals_count: {len(sc['locals'])}")
    print(f"  free_count: {len(free)}")
    print(f"  closure_from_run({len(closure_from_run)}): {closure_from_run}")
    print(f"  sibling_nested_refs({len(sibling_calls)}): {sibling_calls}")
    print(f"  module_or_import_refs({len(module_or_import)}): {module_or_import[:80]}{' ...' if len(module_or_import) > 80 else ''}")
    print(f"  unknown_refs({len(unknown)}): {unknown}")
    print()
