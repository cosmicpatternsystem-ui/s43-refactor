import ast
import re
from pathlib import Path
from collections import defaultdict

TARGET = Path("s43.py")

if not TARGET.exists():
    raise SystemExit("ERROR: s43.py not found")

src = TARGET.read_text(errors="ignore")
lines = src.splitlines()

print("S43 DEEP AUDIT")
print("=" * 70)
print("file:", TARGET)
print("lines:", len(lines))
print()

# -----------------------------
# 1) Parse AST
# -----------------------------
try:
    tree = ast.parse(src)
    print("[OK] AST parse successful")
except SyntaxError as e:
    print("[FAIL] AST parse failed:", e)
    raise SystemExit(2)

print()

# -----------------------------
# 2) Function/class inventory
# -----------------------------
functions = []
classes = []

parent_stack = []

class Inventory(ast.NodeVisitor):
    def visit_ClassDef(self, node):
        classes.append((node.name, node.lineno))
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        functions.append((node.name, node.lineno, "sync"))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        functions.append((node.name, node.lineno, "async"))
        self.generic_visit(node)

Inventory().visit(tree)

print("[INFO] classes:", len(classes))
print("[INFO] functions:", len(functions))
print()

# -----------------------------
# 3) Sensitive definitions
# -----------------------------
sensitive_words = [
    "order", "execute", "submit", "send", "trade", "position",
    "market", "limit", "cancel", "fill", "broker", "exchange"
]

print("SENSITIVE FUNCTION DEFINITIONS")
print("-" * 70)

sensitive_funcs = []
for name, lineno, kind in functions:
    lname = name.lower()
    if any(w in lname for w in sensitive_words):
        sensitive_funcs.append((name, lineno, kind))
        print(f"{lineno:>7}  {kind:<5}  {name}")

if not sensitive_funcs:
    print("none")

print()

# -----------------------------
# 4) Network/API indicators
# -----------------------------
network_patterns = [
    r"\baiohttp\b",
    r"\bClientSession\b",
    r"\brequests\b",
    r"\bhttpx\b",
    r"\burllib\b",
    r"\bwebsocket",
    r"\bws_connect\b",
    r"\.post\s*\(",
    r"\.get\s*\(",
    r"\.request\s*\(",
    r"\.put\s*\(",
    r"\.delete\s*\(",
    r"\.patch\s*\(",
]

print("NETWORK / HTTP INDICATORS")
print("-" * 70)
net_hits = []
for i, line in enumerate(lines, 1):
    for pat in network_patterns:
        if re.search(pat, line, re.I):
            net_hits.append((i, line.strip()))
            print(f"{i:>7}  {line.strip()[:220]}")
            break

if not net_hits:
    print("none")

print()

# -----------------------------
# 5) Exchange endpoint / URL indicators
# -----------------------------
url_patterns = [
    r"https?://",
    r"/api/",
    r"/order",
    r"/orders",
    r"/trade",
    r"/position",
    r"/private",
    r"/account",
    r"/v1/",
    r"/v2/",
    r"/v3/",
    r"/v5/",
    r"binance",
    r"bybit",
    r"okx",
    r"kucoin",
    r"coinbase",
    r"kraken",
    r"bitget",
]

print("URL / EXCHANGE ENDPOINT INDICATORS")
print("-" * 70)
url_hits = []
for i, line in enumerate(lines, 1):
    for pat in url_patterns:
        if re.search(pat, line, re.I):
            url_hits.append((i, line.strip()))
            print(f"{i:>7}  {line.strip()[:220]}")
            break

if not url_hits:
    print("none")

print()

# -----------------------------
# 6) AST call graph context
# -----------------------------
class CallGraph(ast.NodeVisitor):
    def __init__(self):
        self.stack = []
        self.calls = defaultdict(list)

    def visit_FunctionDef(self, node):
        self.stack.append((node.name, node.lineno))
        self.generic_visit(node)
        self.stack.pop()

    def visit_AsyncFunctionDef(self, node):
        self.stack.append((node.name, node.lineno))
        self.generic_visit(node)
        self.stack.pop()

    def visit_Call(self, node):
        if self.stack:
            caller, caller_line = self.stack[-1]
            cname = None
            if isinstance(node.func, ast.Name):
                cname = node.func.id
            elif isinstance(node.func, ast.Attribute):
                cname = node.func.attr
            if cname:
                self.calls[caller].append((cname, getattr(node, "lineno", None)))
        self.generic_visit(node)

cg = CallGraph()
cg.visit(tree)

print("SENSITIVE CALL CHAINS / CALLS")
print("-" * 70)

call_keywords = sensitive_words + [
    "post", "get", "request", "ClientSession", "ws_connect",
    "sign", "headers", "authorization"
]

printed = 0
for caller, calls in cg.calls.items():
    hits = [(c, ln) for c, ln in calls if any(w in c.lower() for w in call_keywords)]
    if hits:
        caller_line = next((ln for n, ln, k in functions if n == caller), "?")
        print(f"\n{caller} @ line {caller_line}")
        for c, ln in hits[:80]:
            print(f"    line {ln}: -> {c}")
        printed += 1

if printed == 0:
    print("none")

print()

# -----------------------------
# 7) Bypass / dynamic execution indicators
# -----------------------------
bypass_patterns = [
    r"\bgetattr\s*\(",
    r"\bsetattr\s*\(",
    r"\bglobals\s*\(",
    r"\blocals\s*\(",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bimportlib\b",
    r"__import__\s*\(",
    r"\basyncio\.create_task\s*\(",
    r"\bensure_future\s*\(",
    r"\bThread\s*\(",
    r"\bProcess\s*\(",
    r"\bsubprocess\b",
]

print("BYPASS / DYNAMIC EXECUTION INDICATORS")
print("-" * 70)
bypass_hits = []
for i, line in enumerate(lines, 1):
    for pat in bypass_patterns:
        if re.search(pat, line):
            bypass_hits.append((i, line.strip()))
            print(f"{i:>7}  {line.strip()[:220]}")
            break

if not bypass_hits:
    print("none")

print()

# -----------------------------
# 8) Safety guard indicators
# -----------------------------
guard_patterns = [
    r"dry_run",
    r"DRY_RUN",
    r"live_trading_armed",
    r"LIVE_TRADING_ARMED",
    r"ai_live_trading_armed",
    r"allow-orders",
    r"AUDIT-ONLY",
    r"AUDIT_ONLY",
    r"ORDER EXECUTION",
    r"SEALED",
    r"quarantine",
    r"quarantined",
]

print("SAFETY GUARD INDICATORS")
print("-" * 70)
guard_hits = []
for i, line in enumerate(lines, 1):
    for pat in guard_patterns:
        if re.search(pat, line, re.I):
            guard_hits.append((i, line.strip()))
            print(f"{i:>7}  {line.strip()[:220]}")
            break

if not guard_hits:
    print("none")

print()

# -----------------------------
# 9) Audit-only patch presence
# -----------------------------
print("AUDIT-ONLY PATCH PRESENCE")
print("-" * 70)

required_markers = [
    "AUDIT-ONLY",
    "S43 SUPER AUTO-SEAL",
    "asyncio.create_task",
    "_audit",
]

for marker in required_markers:
    count = src.count(marker)
    status = "OK" if count else "MISSING"
    print(f"{status:<8} {marker:<30} count={count}")

print()

# -----------------------------
# 10) Risk scoring
# -----------------------------
risk = 0
reasons = []

if sensitive_funcs:
    risk += 2
    reasons.append("sensitive order/execution functions exist")

if net_hits:
    risk += 2
    reasons.append("network/http indicators exist")

if url_hits:
    risk += 1
    reasons.append("exchange/url endpoint indicators exist")

if bypass_hits:
    risk += 2
    reasons.append("dynamic/bypass/background execution indicators exist")

if src.count("AUDIT-ONLY") or src.count("S43 SUPER AUTO-SEAL"):
    risk -= 3
    reasons.append("audit-only/seal markers present")

if src.count("live_trading_armed") or src.count("allow-orders"):
    risk -= 1
    reasons.append("runtime safety gates present")

risk = max(0, min(10, risk))

print("RISK SCORE")
print("-" * 70)
print("score:", risk, "/ 10")
for r in reasons:
    print("-", r)

print()

if risk <= 2:
    verdict = "LOW RISK / LIKELY AUDIT-ONLY"
elif risk <= 5:
    verdict = "MEDIUM RISK / REVIEW REQUIRED"
else:
    verdict = "HIGH RISK / LIVE PATH MAY REMAIN"

print("VERDICT:", verdict)
print("=" * 70)
