import ast
from pathlib import Path
from collections import defaultdict, Counter

PROJECT = Path("s43_project")
OUT = Path("s43_project/architecture/auto_refactor_plan.txt")

class_info = {}
method_info = []  # (class, method, size, tags)
class_methods = defaultdict(list)
class_deps = defaultdict(set)

KEYWORDS = {
    "runtime": ["loop", "event", "schedule", "tick", "async", "sleep", "latency", "rate"],
    "state": ["state", "snapshot", "cache", "store", "journal", "wallet", "position", "balance"],
    "risk": ["risk", "halt", "guard", "breaker", "drawdown", "health", "sanity", "exit"],
    "execution": ["execute", "order", "fill", "cancel", "place", "submit", "normalize"],
    "strategy": ["alpha", "signal", "decision", "model", "filter", "score", "entry", "exit"],
    "market": ["market", "book", "symbol", "tick", "candle", "spread", "depth", "snapshot"],
    "infra": ["client", "http", "api", "request", "response", "retry", "exchange"],
}

def tag_name(name):
    n = name.lower()
    tags = set()
    for tag, words in KEYWORDS.items():
        if any(w in n for w in words):
            tags.add(tag)
    return tags or {"misc"}

class Analyzer(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.current_class = None

    def visit_ClassDef(self, node):
        self.current_class = node.name
        size = (node.end_lineno or node.lineno) - node.lineno + 1
        class_info[node.name] = {
            "file": str(self.filename),
            "lineno": node.lineno,
            "size": size,
        }
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        if self.current_class:
            size = (node.end_lineno or node.lineno) - node.lineno + 1
            tags = tag_name(node.name)
            method_info.append((self.current_class, node.name, size, tags))
            class_methods[self.current_class].append((node.name, size, tags, node.lineno))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Name(self, node):
        if self.current_class and node.id and node.id[0].isupper():
            class_deps[self.current_class].add(node.id)

def scan_file(path):
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        Analyzer(path).visit(tree)
    except Exception:
        pass

for f in PROJECT.rglob("*.py"):
    scan_file(f)

def score_god_class(cls):
    size = class_info.get(cls, {}).get("size", 0)
    mcount = len(class_methods.get(cls, []))
    deps = len(class_deps.get(cls, []))
    tag_counter = Counter()
    big_methods = 0
    for _, msize, tags, _ in class_methods.get(cls, []):
        if msize >= 60:
            big_methods += 1
        tag_counter.update(tags)
    spread = len([k for k,v in tag_counter.items() if v > 0])
    score = size*0.5 + mcount*8 + deps*6 + big_methods*15 + spread*20
    return {
        "size": size,
        "methods": mcount,
        "deps": deps,
        "big_methods": big_methods,
        "concern_spread": spread,
        "tag_counter": tag_counter,
        "score": round(score, 1),
    }

def recommend_splits(cls, stats):
    tags = stats["tag_counter"]
    top = [t for t,_ in tags.most_common()]
    recs = []

    if "runtime" in top:
        recs.append(("TradingBotRuntime", "event loop / scheduling / async orchestration"))
    if "state" in top:
        recs.append(("TradingStateManager", "state / snapshot / cache / wallet / positions"))
    if "risk" in top:
        recs.append(("RiskCoordinator", "risk checks / halt / guard / breaker integration"))
    if "execution" in top:
        recs.append(("ExecutionCoordinator", "order placement / cancel / normalize / fills"))
    if "strategy" in top:
        recs.append(("StrategyCoordinator", "signal / model / decision routing"))
    if "market" in top:
        recs.append(("MarketContext", "market snapshot / symbol / orderbook context"))
    if "infra" in top:
        recs.append(("ExchangeGateway", "client / API / retry / transport wrappers"))

    uniq = []
    seen = set()
    for name,desc in recs:
        if name not in seen:
            uniq.append((name,desc))
            seen.add(name)
    return uniq[:5]

def target_layer(method_name):
    tags = tag_name(method_name)
    priority = ["runtime","state","risk","execution","strategy","market","infra","misc"]
    for p in priority:
        if p in tags:
            return p
    return "misc"

reports = []
reports.append("S43 AUTO REFACTOR PLAN")
reports.append("="*72)

all_stats = []
for cls in class_info:
    st = score_god_class(cls)
    all_stats.append((cls, st))

all_stats.sort(key=lambda x: x[1]["score"], reverse=True)

reports.append("\nTop Refactor Candidates")
reports.append("-"*72)
for cls, st in all_stats[:12]:
    reports.append(
        f"{cls:30} score={st['score']:6} size={st['size']:4} "
        f"methods={st['methods']:3} deps={st['deps']:3} "
        f"big_methods={st['big_methods']:2} concerns={st['concern_spread']}"
    )

reports.append("\nDetailed Split Recommendations")
reports.append("-"*72)

for cls, st in all_stats[:8]:
    reports.append(f"\n[{cls}]")
    reports.append(f"file: {class_info[cls]['file']}")
    reports.append(
        f"size={st['size']} lines, methods={st['methods']}, "
        f"deps={st['deps']}, big_methods={st['big_methods']}, "
        f"concern_spread={st['concern_spread']}, score={st['score']}"
    )
    reports.append("dominant concerns: " + ", ".join(
        f"{k}:{v}" for k,v in st["tag_counter"].most_common()
    ))

    recs = recommend_splits(cls, st)
    if recs:
        reports.append("recommended split:")
        for name, desc in recs:
            reports.append(f"  - {name}: {desc}")
    else:
        reports.append("recommended split: none")

    hot = sorted(class_methods.get(cls, []), key=lambda x: x[1], reverse=True)[:12]
    reports.append("method move suggestions:")
    for mname, msize, tags, lineno in hot:
        layer = target_layer(mname)
        reports.append(
            f"  - {mname:28} {msize:4} lines  -> layer={layer:9} line={lineno}"
        )

reports.append("\nSuggested Target Package Layout")
reports.append("-"*72)
reports.extend([
    "core/        orchestrators, app core, service facades",
    "engine/      execution engines, orchestration engines",
    "strategy/    alpha, signals, decision, models, filters",
    "risk/        risk manager, guards, breakers, health checks",
    "market/      snapshots, symbols, orderbook, specs, stores",
    "runtime/     event loop, schedulers, clocks, rate limiters",
    "infra/       exchange clients, API wrappers, retries, IO",
    "state/       wallet, positions, journals, persistence, caches",
])

reports.append("\nImmediate Refactor Rules")
reports.append("-"*72)
reports.extend([
    "1) Split any class > 800 lines or > 25 methods.",
    "2) Extract any method > 80 lines into helper/service objects.",
    "3) Reduce classes with > 12 dependencies via façade or coordinator.",
    "4) Move exchange/API logic out of orchestration classes into infra gateways.",
    "5) Keep strategy pure: avoid direct IO/network calls inside signal/model code.",
    "6) Isolate state mutation from decision logic.",
])

OUT.write_text("\n".join(reports), encoding="utf-8")
print("Auto refactor plan written to:", OUT)
