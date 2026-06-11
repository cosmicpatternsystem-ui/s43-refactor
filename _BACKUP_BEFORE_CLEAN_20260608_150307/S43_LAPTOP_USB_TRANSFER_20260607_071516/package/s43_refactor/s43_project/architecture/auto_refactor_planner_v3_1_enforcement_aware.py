#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import ast
import math
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

ROOT_DIR = "s43_project"
OUTPUT_FILE = os.path.join(
    ROOT_DIR,
    "architecture",
    "auto_refactor_plan_v3_1_enforcement_aware.txt",
)

EXCLUDE_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules", "dist", "build",
    ".mypy_cache", ".pytest_cache"
}

MAX_FILES = 2000
BIG_METHOD_LINES = 60

NOISE_MODULE_HINTS = {
    "panel", "dashboard", "ui", "telemetry", "render", "console", "view", "screen"
}

NOISE_STRINGS = {
    "hold", "wait", "dashboard", "alert", "status", "screen", "render",
    "warning", "success", "error", "info", "ready", "retrying"
}

SAFETY_BUCKETS = {
    "circuit_breaker": [
        r"\bcircuit[_ ]?breaker\b", r"\bbreaker\b", r"\bhalt\b", r"\bkill[_ ]?switch\b",
        r"\bpanic\b", r"\bpause[_ ]?trading\b", r"\bstop[_ ]?trading\b",
        r"\bfreeze\b", r"\bemergency\b",
    ],
    "stale_data": [
        r"\bstale\b", r"\bfresh(?:ness)?\b", r"\btimestamp\b", r"\bage\b",
        r"\blast_update\b", r"\bexpired\b", r"\boutdated\b", r"\blag\b",
    ],
    "slippage": [
        r"\bslippage\b", r"\bmax[_ ]?slippage\b", r"\bprice[_ ]?impact\b", r"\bimpact\b",
    ],
    "spread": [
        r"\bspread\b", r"\bbid[_ ]?ask\b", r"\bwide[_ ]?market\b", r"\bask\b", r"\bbid\b",
    ],
    "liquidity": [
        r"\bliquidity\b", r"\bdepth\b", r"\borderbook\b", r"\bthin\b", r"\bvolume\b",
    ],
    "account_consistency": [
        r"\breconcile\b", r"\breconciliation\b", r"\bbalance\b", r"\bposition\b",
        r"\bwallet\b", r"\baccount\b", r"\bconsisten(?:cy|t)\b",
        r"\bfilled\b", r"\bfill\b", r"\border[_ ]?state\b",
    ],
    "execution_failsafe": [
        r"\bplace[_ ]?order\b", r"\bsubmit\b", r"\bexecute\b", r"\bcancel\b",
        r"\bretry\b", r"\bbackoff\b", r"\btimeout\b", r"\bverify\b",
        r"\bidempot(?:ent|ency)\b", r"\bunknown[_ ]?status\b", r"\breduce[_ ]?only\b",
    ],
    "volatility_crash": [
        r"\bcrash\b", r"\bbloodbath\b", r"\bvolatil(?:ity|e)\b", r"\bshock\b",
        r"\bmeltdown\b", r"\bpanic[_ ]?sell\b",
    ],
}

CONCERN_PATTERNS = {
    "market": [
        r"\bmarket\b", r"\bticker\b", r"\bdepth\b", r"\borderbook\b",
        r"\bcandle\b", r"\bohlc\b", r"\bsnapshot\b", r"\bspread\b", r"\bsymbol\b",
    ],
    "execution": [
        r"\border\b", r"\bplace_order\b", r"\bsubmit\b", r"\bexecute\b",
        r"\bcancel\b", r"\bfill\b", r"\btrade\b",
    ],
    "account": [
        r"\bbalance\b", r"\bwallet\b", r"\baccount\b", r"\bposition\b",
        r"\bequity\b", r"\bmargin\b",
    ],
    "state": [
        r"\bstate\b", r"\bcache\b", r"\bpersist\b", r"\bload\b", r"\bsave\b",
        r"\bsnapshot\b", r"\bstore\b",
    ],
    "risk": [
        r"\brisk\b", r"\blimit\b", r"\bexposure\b", r"\bdrawdown\b",
        r"\bhalt\b", r"\bbreaker\b", r"\bveto\b",
    ],
    "infra": [
        r"\bhttp\b", r"\brequest\b", r"\bresponse\b", r"\bendpoint\b",
        r"\bclient\b", r"\bsession\b", r"\bretry\b", r"\btransport\b",
        r"\bws\b", r"\bwebsocket\b",
    ],
    "runtime": [
        r"\bloop\b", r"\btask\b", r"\bschedule\b", r"\basync\b", r"\bawait\b",
        r"\bsleep\b", r"\bthread\b", r"\btimer\b",
    ],
    "strategy": [
        r"\bsignal\b", r"\bstrategy\b", r"\balpha\b", r"\bscore\b",
        r"\bdecision\b", r"\bopportunity\b", r"\bentry\b", r"\bexit\b",
    ],
    "telemetry": [
        r"\blog\b", r"\bmetric\b", r"\btelemetry\b", r"\btrace\b", r"\bspan\b",
    ],
    "panel": [
        r"\bpanel\b", r"\bdashboard\b", r"\brender\b", r"\bconsole\b", r"\bview\b",
    ],
    "parser": [
        r"\bparse\b", r"\bjson\b", r"\bdecode\b", r"\bencode\b", r"\bregex\b",
    ],
    "safety": [
        r"\bguard\b", r"\bsafe(?:ty)?\b", r"\breconcile\b", r"\bstale\b",
        r"\bslippage\b", r"\bspread\b", r"\bbreaker\b", r"\bkill[_ ]?switch\b",
        r"\bverify\b", r"\bidempot(?:ent|ency)\b",
    ],
    "core": [
        r"\binit\b", r"\bbase\b", r"\bmanager\b", r"\bcontroller\b", r"\bservice\b",
    ],
}

ENFORCEMENT_GUARD_PATTERNS = {
    "circuit_breaker": [
        r"if .*breaker.*:\s*return",
        r"if .*halt.*:\s*return",
        r"if .*panic.*:\s*return",
        r"if .*kill.*switch.*:\s*return",
        r"raise .*halt",
        r"raise .*emergency",
    ],
    "stale_data": [
        r"if .*stale.*:\s*return",
        r"if .*fresh.* is False.*:\s*return",
        r"if .*timestamp.*<.*:\s*return",
        r"if .*expired.*:\s*return",
        r"raise .*stale",
    ],
    "slippage": [
        r"if .*slippage.*>.*:\s*return",
        r"if .*price[_ ]?impact.*>.*:\s*return",
        r"raise .*slippage",
    ],
    "spread": [
        r"if .*spread.*>.*:\s*return",
        r"if .*bid.*and.*ask.*and.*:\s*return",
        r"raise .*spread",
    ],
    "liquidity": [
        r"if .*liquidity.*<.*:\s*return",
        r"if .*depth.*<.*:\s*return",
        r"if .*volume.*<.*:\s*return",
        r"raise .*liquidity",
    ],
    "account_consistency": [
        r"reconcile\(",
        r"if .*balance.*!=.*:\s*",
        r"if .*position.*!=.*:\s*",
        r"if .*mismatch.*:\s*return",
        r"raise .*recon",
    ],
    "execution_failsafe": [
        r"retry",
        r"backoff",
        r"timeout",
        r"verify",
        r"idempot",
        r"reduce_only",
        r"if .*unknown.*status.*:\s*",
        r"cancel\(",
    ],
    "volatility_crash": [
        r"if .*volatil.*>.*:\s*return",
        r"if .*crash.*:\s*return",
        r"if .*bloodbath.*:\s*return",
        r"raise .*volatil",
    ],
}


@dataclass
class MethodInfo:
    name: str
    lineno: int
    end_lineno: int
    size: int
    source: str
    concern_scores: Dict[str, int] = field(default_factory=dict)
    safety_signal_scores: Dict[str, int] = field(default_factory=dict)
    safety_enforcement_scores: Dict[str, int] = field(default_factory=dict)
    suggested_guards: List[str] = field(default_factory=list)
    primary_concern: str = "core"
    confidence: float = 0.0


@dataclass
class ClassInfo:
    file_path: str
    name: str
    lineno: int
    end_lineno: int
    size: int
    methods: List[MethodInfo] = field(default_factory=list)
    deps: Set[str] = field(default_factory=set)
    concern_scores: Dict[str, int] = field(default_factory=dict)
    safety_signal_scores: Dict[str, int] = field(default_factory=dict)
    safety_enforcement_scores: Dict[str, int] = field(default_factory=dict)
    big_methods: int = 0
    spread: int = 0
    target_package: str = "core"
    target_confidence: float = 0.0
    refactor_score: float = 0.0
    signal_score: float = 0.0
    enforcement_score: float = 0.0
    crash_readiness_score: float = 0.0
    safety_gaps: List[str] = field(default_factory=list)


def normalize_text(s: str) -> str:
    return s.lower()


def is_python_file(path: str) -> bool:
    return path.endswith(".py")


def walk_python_files(root: str) -> List[str]:
    results = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in files:
            if is_python_file(fn):
                results.append(os.path.join(base, fn))
                if len(results) >= MAX_FILES:
                    return results
    return results


def safe_read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return f.read()
    except Exception:
        return ""


def regex_count(patterns: List[str], text: str) -> int:
    total = 0
    for p in patterns:
        total += len(re.findall(p, text, flags=re.IGNORECASE | re.MULTILINE))
    return total


def concern_count(text: str) -> Dict[str, int]:
    return {k: regex_count(patterns, text) for k, patterns in CONCERN_PATTERNS.items()}


def safety_signal_count(text: str) -> Dict[str, int]:
    return {k: regex_count(patterns, text) for k, patterns in SAFETY_BUCKETS.items()}


def safety_enforcement_count(text: str) -> Dict[str, int]:
    return {k: regex_count(patterns, text) for k, patterns in ENFORCEMENT_GUARD_PATTERNS.items()}


def downweight_noise(text: str, file_path: str, counts: Dict[str, int]) -> Dict[str, int]:
    lowered_path = file_path.lower()
    noisy = any(h in lowered_path for h in NOISE_MODULE_HINTS)
    new_counts = dict(counts)

    if noisy:
        for k in list(new_counts.keys()):
            new_counts[k] = int(new_counts[k] * 0.55)

    low = normalize_text(text)
    noise_hits = sum(low.count(s) for s in NOISE_STRINGS)
    if noise_hits > 10:
        for k in list(new_counts.keys()):
            new_counts[k] = int(new_counts[k] * 0.75)

    return new_counts


def top_keys(d: Dict[str, int], n: int = 6) -> List[Tuple[str, int]]:
    return sorted(d.items(), key=lambda x: x[1], reverse=True)[:n]


def choose_primary_concern(scores: Dict[str, int]) -> Tuple[str, float]:
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if not ranked or ranked[0][1] <= 0:
        return "core", 0.0
    top_name, top_score = ranked[0]
    total = sum(v for _, v in ranked) or 1
    return top_name, top_score / total


def map_target_package(primary: str) -> str:
    mapping = {
        "market": "market",
        "execution": "execution",
        "account": "account",
        "state": "state",
        "risk": "safety",
        "infra": "infra",
        "runtime": "runtime",
        "strategy": "strategy",
        "telemetry": "telemetry",
        "panel": "panel",
        "parser": "infra",
        "safety": "safety",
        "core": "runtime",
    }
    return mapping.get(primary, "runtime")


def extract_dependencies(node: ast.ClassDef) -> Set[str]:
    deps = set()

    class Visitor(ast.NodeVisitor):
        def visit_Attribute(self, n):
            if isinstance(n.value, ast.Name) and n.value.id == "self":
                deps.add(n.attr)
            self.generic_visit(n)

        def visit_Name(self, n):
            deps.add(n.id)

    Visitor().visit(node)
    return deps


def get_node_source_lines(source_lines: List[str], node) -> str:
    if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
        return ""
    start = max(node.lineno - 1, 0)
    end = min(node.end_lineno, len(source_lines))
    return "\n".join(source_lines[start:end])


def suggest_guards(method: MethodInfo) -> List[str]:
    suggestions = []
    s = method.safety_signal_scores
    e = method.safety_enforcement_scores
    name = method.name.lower()
    src = method.source.lower()

    def weak(bucket: str) -> bool:
        return s.get(bucket, 0) > 0 and e.get(bucket, 0) == 0

    if "place_order" in name or "submit" in name or "execute" in name:
        if weak("slippage"):
            suggestions.append("inject slippage guard")
        if weak("spread"):
            suggestions.append("inject spread anomaly check")
        if weak("execution_failsafe"):
            suggestions.append("inject idempotency + submit/verify/cancel failsafe")
        if weak("account_consistency"):
            suggestions.append("inject post-trade reconciliation")
        if weak("circuit_breaker"):
            suggestions.append("inject circuit breaker hook")

    if any(k in name for k in ["depth", "orderbook", "snapshot", "ticker"]):
        if weak("stale_data"):
            suggestions.append("inject stale-data/freshness validation")
        if weak("spread"):
            suggestions.append("inject spread anomaly check")
        if weak("liquidity"):
            suggestions.append("inject liquidity guard")
        if weak("volatility_crash"):
            suggestions.append("inject market mode / crash detector hook")

    if any(k in name for k in ["balance", "wallet", "position", "account"]):
        if weak("account_consistency"):
            suggestions.append("inject account consistency / reconcile check")
        if weak("stale_data"):
            suggestions.append("inject state/account freshness check")

    if any(k in name for k in ["load", "save", "state", "snapshot"]):
        if weak("stale_data"):
            suggestions.append("inject state freshness check")
        if weak("circuit_breaker"):
            suggestions.append("inject circuit breaker hook")

    if "reconcile" in src and e.get("account_consistency", 0) == 0:
        suggestions.append("normalize reconciliation into explicit guard-return flow")

    return suggestions


def compute_signal_score(sig: Dict[str, int]) -> float:
    weights = {
        "circuit_breaker": 1.2,
        "stale_data": 1.1,
        "slippage": 1.3,
        "spread": 1.2,
        "liquidity": 1.2,
        "account_consistency": 1.25,
        "execution_failsafe": 1.35,
        "volatility_crash": 1.1,
    }
    raw = sum(sig.get(k, 0) * w for k, w in weights.items())
    return min(100.0, math.log1p(raw) * 14.0)


def compute_enforcement_score(enf: Dict[str, int]) -> float:
    weights = {
        "circuit_breaker": 1.3,
        "stale_data": 1.15,
        "slippage": 1.35,
        "spread": 1.25,
        "liquidity": 1.25,
        "account_consistency": 1.35,
        "execution_failsafe": 1.4,
        "volatility_crash": 1.2,
    }
    raw = sum(enf.get(k, 0) * w for k, w in weights.items())
    return min(100.0, math.log1p(raw) * 18.0)


def compute_crash_readiness(signal_score: float, enforcement_score: float) -> float:
    return round(min(100.0, enforcement_score * 0.72 + signal_score * 0.28), 1)


def compute_refactor_score(cls: ClassInfo) -> float:
    size_score = cls.size * 0.22
    method_score = len(cls.methods) * 8.5
    dep_score = len(cls.deps) * 11.0
    big_score = cls.big_methods * 27.0
    spread_score = cls.spread * 18.0
    low_enforcement_penalty = max(0.0, 75.0 - cls.enforcement_score) * 6.0
    safety_gap_bonus = len(cls.safety_gaps) * 20.0
    return round(
        size_score + method_score + dep_score + big_score + spread_score +
        low_enforcement_penalty + safety_gap_bonus,
        1,
    )


def analyze_method(source_lines: List[str], fn_node) -> MethodInfo:
    src = get_node_source_lines(source_lines, fn_node)
    size = max(0, fn_node.end_lineno - fn_node.lineno + 1)

    concern_scores = concern_count(src)
    sig = safety_signal_count(src)
    enf = safety_enforcement_count(src)
    primary, conf = choose_primary_concern(concern_scores)

    mi = MethodInfo(
        name=fn_node.name,
        lineno=fn_node.lineno,
        end_lineno=fn_node.end_lineno,
        size=size,
        source=src,
        concern_scores=concern_scores,
        safety_signal_scores=sig,
        safety_enforcement_scores=enf,
        primary_concern=primary,
        confidence=round(conf, 2),
    )
    mi.suggested_guards = suggest_guards(mi)
    return mi


def aggregate_counts(items: List[Dict[str, int]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for d in items:
        for k, v in d.items():
            out[k] = out.get(k, 0) + v
    return out


def infer_safety_gaps(sig: Dict[str, int], enf: Dict[str, int]) -> List[str]:
    gaps = []
    for bucket in SAFETY_BUCKETS.keys():
        s = sig.get(bucket, 0)
        e = enf.get(bucket, 0)
        if s >= 2 and e == 0:
            gaps.append(bucket)
        elif s >= 4 and e < max(1, s * 0.15):
            gaps.append(bucket)
    return gaps


def analyze_class(file_path: str, source_lines: List[str], cls_node: ast.ClassDef) -> ClassInfo:
    methods: List[MethodInfo] = []
    for n in cls_node.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and hasattr(n, "end_lineno"):
            methods.append(analyze_method(source_lines, n))

    class_src = get_node_source_lines(source_lines, cls_node)
    class_size = max(0, cls_node.end_lineno - cls_node.lineno + 1)
    deps = extract_dependencies(cls_node)

    concern_scores = aggregate_counts([m.concern_scores for m in methods])
    sig = aggregate_counts([m.safety_signal_scores for m in methods])
    enf = aggregate_counts([m.safety_enforcement_scores for m in methods])

    concern_scores = downweight_noise(class_src, file_path, concern_scores)
    sig = downweight_noise(class_src, file_path, sig)

    big_methods = sum(1 for m in methods if m.size >= BIG_METHOD_LINES)
    spread = sum(1 for v in concern_scores.values() if v > 0)

    primary, conf = choose_primary_concern(concern_scores)
    target = map_target_package(primary)

    cls = ClassInfo(
        file_path=file_path,
        name=cls_node.name,
        lineno=cls_node.lineno,
        end_lineno=cls_node.end_lineno,
        size=class_size,
        methods=methods,
        deps=deps,
        concern_scores=concern_scores,
        safety_signal_scores=sig,
        safety_enforcement_scores=enf,
        big_methods=big_methods,
        spread=spread,
        target_package=target,
        target_confidence=round(conf, 2),
    )

    cls.signal_score = round(compute_signal_score(sig), 1)
    cls.enforcement_score = round(compute_enforcement_score(enf), 1)
    cls.crash_readiness_score = compute_crash_readiness(
        cls.signal_score, cls.enforcement_score
    )
    cls.safety_gaps = infer_safety_gaps(sig, enf)
    cls.refactor_score = compute_refactor_score(cls)
    return cls


def analyze_file(path: str) -> List[ClassInfo]:
    src = safe_read(path)
    if not src.strip():
        return []

    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []

    source_lines = src.splitlines()
    out = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and hasattr(node, "end_lineno"):
            out.append(analyze_class(path, source_lines, node))
    return out


def fmt_top(d: Dict[str, int], n: int = 8) -> str:
    parts = []
    for k, v in top_keys(d, n):
        if v > 0:
            parts.append(f"{k}:{v}")
    return ", ".join(parts) if parts else "-"


def method_line(method: MethodInfo) -> str:
    return (
        f"  - {method.name:<30} {method.size:>4} lines -> {method.primary_concern:<10} "
        f"conf={method.confidence:.2f} line={method.lineno} "
        f"| signal={sum(method.safety_signal_scores.values())} "
        f"enf={sum(method.safety_enforcement_scores.values())}"
        + (
            f" | guards: {'; '.join(method.suggested_guards)}"
            if method.suggested_guards else ""
        )
    )


def build_summary(classes: List[ClassInfo]) -> str:
    lines = []
    lines.append("Top Refactor Candidates")
    lines.append("-" * 100)

    for c in sorted(classes, key=lambda x: x.refactor_score, reverse=True)[:20]:
        lines.append(
            f"{c.name:<30} score={c.refactor_score:>7.1f} size={c.size:>4} "
            f"methods={len(c.methods):>3} deps={len(c.deps):>3} big={c.big_methods:>2} "
            f"spread={c.spread:>2} target={c.target_package:<10} conf={c.target_confidence:.2f} "
            f"signal={c.signal_score:>5.1f} enf={c.enforcement_score:>5.1f} "
            f"crash_ready={c.crash_readiness_score:>5.1f}"
        )

    global_sig = aggregate_counts([c.safety_signal_scores for c in classes])
    global_enf = aggregate_counts([c.safety_enforcement_scores for c in classes])

    lines.append("")
    lines.append("Crash Safety Summary")
    lines.append("-" * 100)
    for bucket in SAFETY_BUCKETS.keys():
        s = global_sig.get(bucket, 0)
        e = global_enf.get(bucket, 0)
        ratio = 0.0 if s == 0 else round(e / s, 2)
        lines.append(
            f"{bucket:<22} signals={s:<6} enforcement={e:<6} enforcement_ratio={ratio:.2f}"
        )

    lines.append("")
    lines.append("Priority Hardening Heuristics")
    lines.append("-" * 100)
    lines.append("1) execution paths with high signal / low enforcement")
    lines.append("2) account reconciliation and balance freshness")
    lines.append("3) stale market data, spread, and liquidity guards")
    lines.append("4) remove UI/panel/telemetry from hot execution paths")
    return "\n".join(lines)


def build_class_section(c: ClassInfo) -> str:
    lines = []
    lines.append(f"[{c.name}]")
    lines.append(f"file: {c.file_path}")
    lines.append(
        f"size={c.size} lines | methods={len(c.methods)} | deps={len(c.deps)} "
        f"| big_methods={c.big_methods} | spread={c.spread} | score={c.refactor_score}"
    )
    lines.append(
        f"recommended package: {c.target_package} (confidence={c.target_confidence:.2f})"
    )
    lines.append(
        f"signal score: {c.signal_score}/100 | enforcement score: {c.enforcement_score}/100 "
        f"| crash readiness score: {c.crash_readiness_score}/100"
    )
    lines.append(f"dominant concerns: {fmt_top(c.concern_scores, 8)}")
    lines.append(f"safety signals: {fmt_top(c.safety_signal_scores, 8)}")
    lines.append(f"safety enforcement: {fmt_top(c.safety_enforcement_scores, 8)}")
    lines.append("safety gaps: " + (", ".join(c.safety_gaps) if c.safety_gaps else "-"))

    lines.append("split recommendation:")
    inserts = []
    if any(c.concern_scores.get(k, 0) > 0 for k in ("strategy", "execution")):
        inserts.extend([
            "  - StrategyCoordinator: signal / model / decision routing",
            "  - ExecutionService: submit / verify / cancel / idempotency",
        ])

    default_splits = [
        "  - SafetyCoordinator: crash/panic protection, guards, kill-switch escalation",
        "  - RiskCoordinator: risk checks / halt / breaker / emergency rules",
        "  - MarketContext: market snapshot / orderbook / symbol context",
        "  - TradingStateManager: wallet / positions / cache / save-load",
        "  - ExchangeGateway: API transport / retry / endpoint wrappers",
        "  - TradingBotRuntime: event loop / async scheduling / timing",
    ]
    lines.extend(inserts + default_splits)

    lines.append("critical method guard suggestions:")
    critical = sorted(c.methods, key=lambda m: m.size, reverse=True)[:12]
    for m in critical:
        if m.size >= 20:
            lines.append(method_line(m))

    lines.append("signal-heavy / enforcement-weak methods:")
    weak = []
    for m in c.methods:
        s = sum(m.safety_signal_scores.values())
        e = sum(m.safety_enforcement_scores.values())
        if s >= 3 and e == 0:
            weak.append((s, m))

    for _, m in sorted(weak, key=lambda x: x[0], reverse=True)[:10]:
        lines.append(
            f"  - {m.name:<30} signal={sum(m.safety_signal_scores.values())} "
            f"enf={sum(m.safety_enforcement_scores.values())} line={m.lineno}"
        )

    return "\n".join(lines)


def build_report(classes: List[ClassInfo]) -> str:
    sections = [build_summary(classes), "", "Detailed Recommendations", "-" * 100]
    for c in sorted(classes, key=lambda x: x.refactor_score, reverse=True)[:30]:
        sections.append("")
        sections.append(build_class_section(c))
    return "\n".join(sections)


def main():
    files = walk_python_files(ROOT_DIR)
    all_classes: List[ClassInfo] = []

    for path in files:
        all_classes.extend(analyze_file(path))

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    report = build_report(all_classes)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[OK] analyzed files: {len(files)}")
    print(f"[OK] classes found: {len(all_classes)}")
    print(f"[OK] report written: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
