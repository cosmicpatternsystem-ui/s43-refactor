import ast
from pathlib import Path
from collections import defaultdict

FILE = "s43_dev_next.py"

STAGE_KEYWORDS = {
    "SIGNAL": ("signal", "alpha", "entry", "setup", "trigger"),
    "RISK": ("risk", "halt", "guard", "block", "exposure"),
    "SIZE": ("size", "sizer", "kelly", "qty", "quantity", "volume"),
    "ORDER": ("order", "place", "submit", "cancel", "ladder"),
    "EXECUTION": ("execute", "trade", "fill"),
    "EXCHANGE": ("exchange", "client", "request", "api", "_ex"),
}

src = Path(FILE).read_text(encoding="utf-8")
tree = ast.parse(src)

func_lines = {}
calls_map = defaultdict(set)

def get_call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parts = []
        cur = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        parts.reverse()
        return ".".join(parts)
    return None

class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.current = None

    def visit_FunctionDef(self, node):
        prev = self.current
        self.current = node.name
        func_lines[node.name] = node.lineno
        self.generic_visit(node)
        self.current = prev

    def visit_AsyncFunctionDef(self, node):
        prev = self.current
        self.current = node.name
        func_lines[node.name] = node.lineno
        self.generic_visit(node)
        self.current = prev

    def visit_Call(self, node):
        if self.current:
            name = get_call_name(node.func)
            if name:
                calls_map[self.current].add(name)
        self.generic_visit(node)

Visitor().visit(tree)

def stage_of(name: str):
    low = name.lower()
    matched = []
    for stage, kws in STAGE_KEYWORDS.items():
        if any(k in low for k in kws):
            matched.append(stage)
    return matched

interesting_funcs = []
for fn in func_lines:
    stages = stage_of(fn)
    if stages:
        interesting_funcs.append((fn, func_lines[fn], stages))

print("===== ORDER FLOW STAGE MAP =====")
for fn, line, stages in sorted(interesting_funcs, key=lambda x: x[1]):
    print(f"{line:5d}  {fn:35s}  [{' | '.join(stages)}]")

print("\n===== STAGE TRANSITIONS =====")
for fn, line, stages in sorted(interesting_funcs, key=lambda x: x[1]):
    transitions = []
    for callee in sorted(calls_map.get(fn, [])):
        callee_stages = stage_of(callee)
        if callee_stages:
            transitions.append((callee, callee_stages))
    if transitions:
        print(f"\n--- {fn} (line {line}) [{' | '.join(stages)}] ---")
        for callee, callee_stages in transitions:
            print(f"  -> {callee:40s} [{' | '.join(callee_stages)}]")

print("\n===== HIGH PRIORITY ORDER FLOW =====")
focus = [
    "filter_signal",
    "_get_raw_signal",
    "should_trade",
    "should_execute",
    "can_execute",
    "execute_order_v121",
    "_execute_trade",
    "place_limit",
    "place_market",
    "place_order",
    "_place_order_impl",
    "cancel_order",
    "cancel_all_orders",
]
for name in focus:
    if name in func_lines:
        print(f"\n### {name} (line {func_lines[name]}) [{' | '.join(stage_of(name))}]")
        for callee in sorted(calls_map.get(name, [])):
            st = stage_of(callee)
            if st:
                print(f"   -> {callee:40s} [{' | '.join(st)}]")

print("\n===== POSSIBLE TERMINAL EXCHANGE CALLS =====")
for fn, line, _stages in sorted(interesting_funcs, key=lambda x: x[1]):
    hits = []
    for callee in sorted(calls_map.get(fn, [])):
        low = callee.lower()
        if (
            "place_order" in low
            or "cancel_order" in low
            or "cancel_all_orders" in low
            or "list_orders" in low
            or "request" in low
            or "api" in low
            or "client" in low
            or "self._ex." in low
            or "w.ex." in low
        ):
            hits.append(callee)
    if hits:
        print(f"\n--- {fn} (line {line}) ---")
        for h in hits:
            print(f"  TERMINAL? -> {h}")
