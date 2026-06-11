import ast
import re
from pathlib import Path
from collections import defaultdict, Counter

PROJECT = Path("s43_project")
OUT = Path("s43_project/architecture/auto_refactor_plan_v3_crash_aware.txt")

CLASS_INFO = {}
CLASS_METHODS = defaultdict(list)
CLASS_DEPS = defaultdict(set)
CLASS_SIGNALS = defaultdict(Counter)
METHOD_SIGNALS = defaultdict(Counter)
CLASS_STRINGS = defaultdict(list)
METHOD_CALLS = defaultdict(list)
METHOD_ATTRS = defaultdict(list)

LAYER_KEYWORDS = {
    "core": [
        "bot","core","coordinator","orchestrator","controller","manager","service"
    ],
    "runtime": [
        "run","loop","runtime","tick","event","schedule","scheduler","clock",
        "async","await","sleep","latency","interval","throttle","rate_limit"
    ],
    "strategy": [
        "alpha","signal","strategy","model","decision","score","filter","entry",
        "exit","predict","forecast","rank","phoenix","cortex"
    ],
    "risk": [
        "risk","halt","breaker","guard","drawdown","sanity","kill","stoploss",
        "exposure","var","liquidation","emergency"
    ],
    "execution": [
        "execute","execution","order","fill","cancel","submit","place","amend",
        "replace","trade","post_only","reduce_only"
    ],
    "market": [
        "market","symbol","ticker","tick","spread","depth","book","orderbook",
        "candle","klines","ohlcv","tradefeed","snapshot","bid","ask","mid"
    ],
    "state": [
        "state","wallet","position","portfolio","journal","persistence","persist",
        "cache","store","restore","save","load","ledger","balance"
    ],
    "infra": [
        "client","api","http","https","request","response","gateway","transport",
        "session","retry","rest","websocket","ws","exchange","endpoint","timeout"
    ],
    "parser": [
        "parse","normalize","transform","decode","encode","serialize","deserialize",
        "mapper","schema","adapt","adapter","format"
    ],
    "account": [
        "account","wallet","balance","equity","margin","asset","assets","pnl",
        "available","locked","funding","collateral"
    ],
    "telemetry": [
        "log","logger","metric","metrics","trace","tracing","monitor","alert",
        "report","stats","debug","health","audit"
    ],
    "ui": [
        "render","screen","view","display","print","stdout","ansi","terminal"
    ],
    "panel": [
        "panel","dashboard","table","layout","widget","rich","console"
    ],
    "safety": [
        "crash","panic","bloodbath","failsafe","fail_safe","kill_switch","killswitch",
        "circuit_breaker","breaker","stale","freshness","consistency","reconcile",
        "slippage","spread_guard","liquidity","de_risk","derisk","reduce_only",
        "exit_only","volatility","shock","collapse","freeze","pause","guard"
    ],
}

SAFETY_AREAS = {
    "circuit_breaker": [
        "circuit_breaker","breaker","halt","pause","kill_switch","killswitch",
        "exit_only","reduce_only","freeze_trading"
    ],
    "stale_data": [
        "stale","fresh","freshness","lag","latency","sequence_gap","timestamp_drift",
        "ws_stale","feed_age","last_update","outdated"
    ],
    "slippage": [
        "slippage","impact","sweep_cost","max_slippage","price_impact"
    ],
    "spread": [
        "spread","bid_ask","wide_market","mid_price","relative_spread"
    ],
    "liquidity": [
        "liquidity","depth","orderbook_hole","top_of_book","book_thin","imbalance"
    ],
    "account_consistency": [
        "reconcile","reconciliation","consistency","sync_account","sync_position",
        "position_mismatch","balance_mismatch","unknown_order_state"
    ],
    "execution_failsafe": [
        "idempotent","idempotency","retry","backoff","timeout","dedup","deduplicate",
        "post_submit_verify","cancel_confirm","partial_fill","unknown_order_state"
    ],
    "volatility_crash": [
        "volatility","atr","shock","crash","panic","drawdown","collapse","fast_drop"
    ],
}

CRITICAL_METHOD_HINTS = {
    "execution": [
        "place_order","submit_order","cancel_order","amend_order","replace_order",
        "close_position","open_position","create_order"
    ],
    "market": [
        "fetch_depth","get_depth","snapshot","get_market_snapshot","fetch_ticker",
        "get_book","orderbook","fetch_spot"
    ],
    "state": [
        "_refresh_balance_if_needed","get_balance","load_state","save_state",
        "_load_state","_save_state","restore","reconcile"
    ],
    "runtime": [
        "_run","run","main_loop","tick","step"
    ]
}

PRIORITY = [
    "safety","strategy","risk","execution","market","state","infra","runtime",
    "parser","account","telemetry","ui","panel","core"
]

def tokenize(text):
    text = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)
    parts = re.split(r'[^a-zA-Z0-9_]+', text.lower())
    out = []
    for p in parts:
        if not p:
            continue
        out.extend(p.split("_"))
    return [x for x in out if x]

def score_tokens(tokens, keyword_map):
    c = Counter()
    for t in tokens:
        for layer, kws in keyword_map.items():
            for kw in kws:
                if kw in t or t in kw:
                    c[layer] += 1
    return c

def merge_counter(dst, src, weight=1):
    for k, v in src.items():
        dst[k] += v * weight

class SignalVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.current_class = None
        self.current_method = None

    def visit_ClassDef(self, node):
        self.current_class = node.name
        size = (node.end_lineno or node.lineno) - node.lineno + 1
        CLASS_INFO[node.name] = {
            "file": str(self.filename),
            "lineno": node.lineno,
            "size": size,
        }
        merge_counter(CLASS_SIGNALS[node.name], score_tokens(tokenize(node.name), LAYER_KEYWORDS), 4)

        for base in node.bases:
            if isinstance(base, ast.Name):
                CLASS_DEPS[node.name].add(base.id)
                merge_counter(CLASS_SIGNALS[node.name], score_tokens(tokenize(base.id), LAYER_KEYWORDS), 2)
            elif isinstance(base, ast.Attribute):
                merge_counter(CLASS_SIGNALS[node.name], score_tokens(tokenize(base.attr), LAYER_KEYWORDS), 2)

        self.generic_visit(node)
        self.current_class = None

    def handle_function(self, node):
        if not self.current_class:
            return

        self.current_method = node.name
        size = (node.end_lineno or node.lineno) - node.lineno + 1

        method_sig = Counter()
        merge_counter(method_sig, score_tokens(tokenize(node.name), LAYER_KEYWORDS), 5)

        for arg in node.args.args:
            merge_counter(method_sig, score_tokens(tokenize(arg.arg), LAYER_KEYWORDS), 1)

        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                merge_counter(method_sig, score_tokens(tokenize(dec.id), LAYER_KEYWORDS), 1)

        METHOD_SIGNALS[(self.current_class, node.name)] = method_sig
        CLASS_METHODS[self.current_class].append({
            "name": node.name,
            "size": size,
            "lineno": node.lineno,
            "signals": method_sig,
        })
        merge_counter(CLASS_SIGNALS[self.current_class], method_sig, 1)

        self.generic_visit(node)
        self.current_method = None

    def visit_FunctionDef(self, node):
        self.handle_function(node)

    def visit_AsyncFunctionDef(self, node):
        self.handle_function(node)

    def visit_Attribute(self, node):
        if self.current_class:
            token_scores = score_tokens(tokenize(node.attr), LAYER_KEYWORDS)
            merge_counter(CLASS_SIGNALS[self.current_class], token_scores, 1)
            if self.current_method:
                METHOD_ATTRS[(self.current_class, self.current_method)].append(node.attr)
        self.generic_visit(node)

    def visit_Call(self, node):
        if self.current_class:
            if isinstance(node.func, ast.Name):
                fname = node.func.id
                merge_counter(CLASS_SIGNALS[self.current_class], score_tokens(tokenize(fname), LAYER_KEYWORDS), 2)
                if self.current_method:
                    METHOD_CALLS[(self.current_class, self.current_method)].append(fname)
            elif isinstance(node.func, ast.Attribute):
                fname = node.func.attr
                merge_counter(CLASS_SIGNALS[self.current_class], score_tokens(tokenize(fname), LAYER_KEYWORDS), 2)
                if self.current_method:
                    METHOD_CALLS[(self.current_class, self.current_method)].append(fname)
        self.generic_visit(node)

    def visit_Name(self, node):
        if self.current_class and node.id and node.id[:1].isupper():
            CLASS_DEPS[self.current_class].add(node.id)
            merge_counter(CLASS_SIGNALS[self.current_class], score_tokens(tokenize(node.id), LAYER_KEYWORDS), 1)

    def visit_Constant(self, node):
        if self.current_class and isinstance(node.value, str):
            toks = tokenize(node.value)
            sig = score_tokens(toks, LAYER_KEYWORDS)
            merge_counter(CLASS_SIGNALS[self.current_class], sig, 1)
            if len(toks) <= 14:
                CLASS_STRINGS[self.current_class].append(node.value[:120])

def scan_file(path):
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        SignalVisitor(path).visit(tree)
    except Exception:
        pass

for f in PROJECT.rglob("*.py"):
    if "architecture" in str(f):
        continue
    scan_file(f)

def concern_summary(counter):
    items = [(k, v) for k, v in counter.items() if v > 0]
    items.sort(key=lambda x: x[1], reverse=True)
    return items

def best_layer(counter):
    items = concern_summary(counter)
    if not items:
        return "core", 0.0, []

    filtered = [(k, v) for k, v in items if k != "core" or v >= 3]
    if not filtered:
        filtered = items

    top_layer, top_score = filtered[0]
    total = sum(v for _, v in filtered) or 1
    second_score = filtered[1][1] if len(filtered) > 1 else 0
    confidence = top_score / total

    if top_score <= second_score + 1 and top_layer == "core" and len(filtered) > 1:
        top_layer = filtered[1][0]
        top_score = filtered[1][1]
        confidence = top_score / total

    return top_layer, round(confidence, 3), filtered[:8]

def score_god_class(cls):
    info = CLASS_INFO.get(cls, {})
    size = info.get("size", 0)
    methods = CLASS_METHODS.get(cls, [])
    mcount = len(methods)
    deps = len(CLASS_DEPS.get(cls, []))
    big_methods = len([m for m in methods if m["size"] >= 80])

    concerns = concern_summary(CLASS_SIGNALS[cls])
    spread = len([1 for _, v in concerns[:10] if v > 0])

    score = (
        size * 0.45 +
        mcount * 9 +
        deps * 7 +
        big_methods * 20 +
        spread * 18
    )
    return {
        "size": size,
        "methods": mcount,
        "deps": deps,
        "big_methods": big_methods,
        "concern_spread": spread,
        "score": round(score, 1),
        "concerns": concerns,
    }

def collect_method_tokens(cls, method_name):
    toks = []
    toks.extend(tokenize(method_name))
    for c in METHOD_CALLS.get((cls, method_name), []):
        toks.extend(tokenize(c))
    for a in METHOD_ATTRS.get((cls, method_name), []):
        toks.extend(tokenize(a))
    return toks

def safety_scores_for_tokens(tokens):
    return score_tokens(tokens, SAFETY_AREAS)

def safety_profile_for_class(cls):
    total = Counter()
    for m in CLASS_METHODS.get(cls, []):
        toks = collect_method_tokens(cls, m["name"])
        merge_counter(total, safety_scores_for_tokens(toks), 1)

    for s in CLASS_STRINGS.get(cls, []):
        merge_counter(total, safety_scores_for_tokens(tokenize(s)), 1)

    return total

def crash_readiness_score(cls):
    sp = safety_profile_for_class(cls)
    found_areas = sum(1 for _, v in sp.items() if v > 0)
    method_count = max(1, len(CLASS_METHODS.get(cls, [])))
    coverage = found_areas / max(1, len(SAFETY_AREAS))
    density = sum(sp.values()) / method_count
    raw = coverage * 65 + min(density, 6) * 5.5
    return round(min(raw, 100), 1), sp

def recommend_splits(cls, stats):
    concerns = [k for k, _ in stats["concerns"][:10]]
    recs = []

    mapping = {
        "safety": ("SafetyCoordinator", "crash/panic protection, guards, kill-switch escalation"),
        "runtime": ("TradingBotRuntime", "event loop / async scheduling / timing"),
        "state": ("TradingStateManager", "wallet / positions / cache / save-load"),
        "risk": ("RiskCoordinator", "risk checks / halt / breaker / emergency rules"),
        "execution": ("ExecutionCoordinator", "order placement / amend / cancel / fill flow"),
        "strategy": ("StrategyCoordinator", "signal / model / decision routing"),
        "market": ("MarketContext", "market snapshot / orderbook / symbol context"),
        "infra": ("ExchangeGateway", "API transport / retry / endpoint wrappers"),
        "parser": ("PayloadParser", "normalize / parse / transform / adapt payloads"),
        "account": ("AccountService", "balance / equity / margin / pnl concerns"),
        "telemetry": ("TelemetryService", "logs / metrics / health / stats"),
        "ui": ("TerminalView", "rendering / terminal output"),
        "panel": ("DashboardPanel", "panel/layout/table/dashboard rendering"),
    }

    for c in PRIORITY:
        if c in concerns and c in mapping:
            recs.append(mapping[c])

    uniq = []
    seen = set()
    for a, b in recs:
        if a not in seen:
            uniq.append((a, b))
            seen.add(a)
    return uniq[:7]

def method_target_layer(method):
    counter = Counter()
    merge_counter(counter, score_tokens(tokenize(method["name"]), LAYER_KEYWORDS), 5)
    merge_counter(counter, method["signals"], 1)
    layer, conf, top = best_layer(counter)
    return layer, conf, top

def method_guard_suggestions(cls, method):
    toks = collect_method_tokens(cls, method["name"])
    joined = " ".join(toks + tokenize(method["name"]))
    suggestions = []

    exec_hits = any(h in method["name"] for h in CRITICAL_METHOD_HINTS["execution"]) or any(
        x in joined for x in ["order", "cancel", "submit", "amend", "replace", "fill", "trade"]
    )
    market_hits = any(h in method["name"] for h in CRITICAL_METHOD_HINTS["market"]) or any(
        x in joined for x in ["depth", "book", "ticker", "spread", "snapshot", "bid", "ask"]
    )
    state_hits = any(h in method["name"] for h in CRITICAL_METHOD_HINTS["state"]) or any(
        x in joined for x in ["balance", "position", "wallet", "state", "save", "load", "reconcile"]
    )
    runtime_hits = any(h in method["name"] for h in CRITICAL_METHOD_HINTS["runtime"]) or any(
        x in joined for x in ["run", "loop", "tick", "schedule"]
    )

    safety_present = safety_scores_for_tokens(toks)

    if exec_hits:
        if safety_present["slippage"] == 0:
            suggestions.append("inject slippage guard")
        if safety_present["spread"] == 0:
            suggestions.append("inject spread guard")
        if safety_present["execution_failsafe"] == 0:
            suggestions.append("inject execution failsafe (idempotency/retry/verify)")
        if safety_present["account_consistency"] == 0:
            suggestions.append("inject post-trade reconciliation")

    if market_hits:
        if safety_present["stale_data"] == 0:
            suggestions.append("inject stale-data/freshness validation")
        if safety_present["liquidity"] == 0:
            suggestions.append("inject liquidity guard")
        if safety_present["spread"] == 0:
            suggestions.append("inject spread anomaly check")

    if state_hits:
        if safety_present["account_consistency"] == 0:
            suggestions.append("inject account consistency / reconcile check")
        if safety_present["stale_data"] == 0:
            suggestions.append("inject state freshness check")

    if runtime_hits:
        if safety_present["circuit_breaker"] == 0:
            suggestions.append("inject circuit breaker hook")
        if safety_present["volatility_crash"] == 0:
            suggestions.append("inject market mode / crash detector hook")

    uniq = []
    seen = set()
    for s in suggestions:
        if s not in seen:
            uniq.append(s)
            seen.add(s)
    return uniq[:5]

def safety_gaps(cls):
    score, sp = crash_readiness_score(cls)
    missing = []
    for area in SAFETY_AREAS:
        if sp[area] == 0:
            missing.append(area)
    return score, sp, missing

REPORT = []
REPORT.append("S43 AUTO REFACTOR PLAN V3 - CRASH AWARE")
REPORT.append("=" * 100)
REPORT.append("Architecture + crash readiness + safety gap analysis + guard injection suggestions")
REPORT.append("")

all_stats = []
for cls in CLASS_INFO:
    st = score_god_class(cls)
    layer, conf, top = best_layer(CLASS_SIGNALS[cls])
    crash_score, sp = crash_readiness_score(cls)
    all_stats.append((cls, st, layer, conf, top, crash_score, sp))

all_stats.sort(key=lambda x: (x[1]["score"], -x[5]), reverse=True)

REPORT.append("Top Refactor Candidates")
REPORT.append("-" * 100)
for cls, st, layer, conf, top, crash_score, sp in all_stats[:20]:
    REPORT.append(
        f"{cls:30} score={st['score']:7} size={st['size']:4} methods={st['methods']:3} "
        f"deps={st['deps']:3} big={st['big_methods']:2} spread={st['concern_spread']:2} "
        f"target={layer:10} conf={conf:.2f} crash_ready={crash_score:5.1f}"
    )

REPORT.append("")
REPORT.append("Crash Readiness Summary")
REPORT.append("-" * 100)
global_safety = Counter()
for cls in CLASS_INFO:
    _, sp = crash_readiness_score(cls)
    merge_counter(global_safety, sp)

for area in SAFETY_AREAS:
    REPORT.append(f"{area:22} signals={global_safety[area]}")

REPORT.append("")
REPORT.append("Detailed Recommendations")
REPORT.append("-" * 100)

for cls, st, layer, conf, top, crash_score, sp in all_stats[:12]:
    REPORT.append(f"\n[{cls}]")
    REPORT.append(f"file: {CLASS_INFO[cls]['file']}")
    REPORT.append(
        f"size={st['size']} lines | methods={st['methods']} | deps={st['deps']} | "
        f"big_methods={st['big_methods']} | spread={st['concern_spread']} | score={st['score']}"
    )
    REPORT.append(f"recommended package: {layer}  (confidence={conf:.2f})")
    REPORT.append(f"crash readiness score: {crash_score}/100")
    REPORT.append("dominant concerns: " + ", ".join(f"{k}:{v}" for k, v in top))
    REPORT.append("safety signals: " + ", ".join(f"{k}:{v}" for k, v in sp.items() if v > 0) if any(v > 0 for v in sp.values()) else "safety signals: none")

    split_recs = recommend_splits(cls, st)
    if split_recs:
        REPORT.append("split recommendation:")
        for name, desc in split_recs:
            REPORT.append(f"  - {name}: {desc}")
    else:
        REPORT.append("split recommendation: none")

    score, spx, missing = safety_gaps(cls)
    REPORT.append("safety gaps:")
    for m in missing[:8]:
        REPORT.append(f"  - missing: {m}")

    hot_methods = sorted(CLASS_METHODS[cls], key=lambda x: x["size"], reverse=True)[:12]
    REPORT.append("critical method guard suggestions:")
    for m in hot_methods:
        mlayer, mconf, mtop = method_target_layer(m)
        guards = method_guard_suggestions(cls, m)
        top_txt = ", ".join(f"{k}:{v}" for k, v in mtop[:3])
        guard_txt = "; ".join(guards) if guards else "no immediate guard suggestion"
        REPORT.append(
            f"  - {m['name']:30} {m['size']:4} lines -> {mlayer:10} conf={mconf:.2f} line={m['lineno']} "
            f"[{top_txt}] | guards: {guard_txt}"
        )

    if CLASS_STRINGS[cls]:
        REPORT.append("signal strings:")
        for s in CLASS_STRINGS[cls][:6]:
            REPORT.append(f"  - {s}")

REPORT.append("")
REPORT.append("Bloodbath Refactor Priorities")
REPORT.append("-" * 100)
REPORT.extend([
    "1) Harden execution paths first: place/cancel/amend/replace/verify/reconcile.",
    "2) Add stale-data and freshness validation to all market/state critical paths.",
    "3) Enforce account consistency before any new exposure increase.",
    "4) Integrate circuit breaker hooks into runtime loop and strategy dispatch.",
    "5) Add market mode classification: NORMAL / FAST_DROP / PANIC / ILLIQUID / DISLOCATED / API_UNSTABLE.",
    "6) Separate safety logic from risk logic; create safety/ package.",
    "7) Extract parser/normalizer code from transport and execution flows.",
    "8) Move rendering/panel/telemetry out of orchestration hot paths.",
])

REPORT.append("")
REPORT.append("Suggested Safety Package Layout")
REPORT.append("-" * 100)
REPORT.extend([
    "safety/",
    "  market_mode_classifier.py",
    "  crash_detector.py",
    "  circuit_breaker.py",
    "  stale_data_guard.py",
    "  spread_guard.py",
    "  liquidity_guard.py",
    "  slippage_guard.py",
    "  account_consistency_guard.py",
    "  execution_failsafe.py",
    "  position_derisker.py",
    "  kill_switch.py",
])

REPORT.append("")
REPORT.append("Refactor Rules")
REPORT.append("-" * 100)
REPORT.extend([
    "1) Split any class > 800 lines or > 25 methods.",
    "2) Extract any method > 80 lines into helper/service objects.",
    "3) Reduce classes with > 12 dependencies via façade/coordinator.",
    "4) Move API/network/retry logic into infra gateways.",
    "5) Keep strategy/model/signal code pure and IO-free.",
    "6) Isolate state mutation from decision logic.",
    "7) Add guard hooks to every critical execution and state-refresh path.",
    "8) No new exposure when data is stale or account consistency is uncertain.",
    "9) In panic/illiquid modes, switch to reduce-only or exit-only behavior.",
    "10) Keep survival logic in safety/, not inside monolithic orchestrators.",
])

OUT.write_text("\n".join(REPORT), encoding="utf-8")
print("Written:", OUT)
