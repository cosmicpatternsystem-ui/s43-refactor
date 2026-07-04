#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ASO-X Auto Pilot

Production posture:
- Safe by default
- Cycle-limited execution
- Kill-switch aware
- Dry-run capable
- JSONL action ledger
- Standard library only
"""

from __future__ import annotations
try:
    from tools.policy_matrix import PolicyInput, evaluate_policy_input
except ModuleNotFoundError:
    # Direct script execution: python tools/auto_pilot.py
    from policy_matrix import PolicyInput, evaluate_policy_input

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = REPO_ROOT / ".runtime"
DEFAULT_LEDGER_PATH = RUNTIME_DIR / "autopilot_actions.jsonl"
DEFAULT_KILL_SWITCH_PATH = RUNTIME_DIR / "autopilot.kill"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def cp_safe_print(message: str) -> None:
    """
    Keep stdout friendly for Windows/cp1252 terminals.
    Avoid symbols that may fail in legacy consoles.
    """
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode("ascii", errors="replace").decode("ascii"))


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    """
    Append a single JSON object as one JSONL line.

    Notes:
    - UTF-8 without BOM by default in Python when encoding='utf-8'.
    - newline='\\n' keeps LF discipline.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")
        handle.flush()


def kill_switch_active(path: Path) -> bool:
    return path.exists()


def check_guardian_reports() -> dict[str, Any]:
    """
    Placeholder for future Guardian integration.

    This function must remain side-effect-light unless explicitly approved
    by policy. For now it returns a deterministic status payload.
    """
    return {
        "component": "guardian",
        "status": "not_integrated",
    }


def apply_policy_rules(report: dict[str, Any]) -> dict[str, Any]:
    """
    Placeholder for future Policy Engine integration.

    Future behavior:
    - classify proposed actions
    - block unsafe actions
    - require operator approval for sensitive actions
    """
    return {
        "component": "policy_engine",
        "status": "not_integrated",
        "allowed": True,
        "input_status": report.get("status", "unknown"),
    }


def run_cycle(*, cycle: int, dry_run: bool, ledger_path: Path) -> int:
    """
    Execute exactly one autopilot cycle.

    Return codes:
    - 0: success
    - 2: controlled failure
    """
    append_jsonl(
        ledger_path,
        {
            "ts": utc_now_iso(),
            "event": "cycle_start",
            "cycle": cycle,
            "dry_run": dry_run,
        },
    )

    try:
        guardian_report = check_guardian_reports()
        policy_result = apply_policy_rules(guardian_report)

        if dry_run:
            action = "dry_run_noop"
        else:
            action = "noop"

        append_jsonl(
            ledger_path,
            {
                "ts": utc_now_iso(),
                "event": "action",
                "cycle": cycle,
                "action": action,
                "guardian_status": guardian_report.get("status"),
                "policy_status": policy_result.get("status"),
                "policy_allowed": policy_result.get("allowed"),
                "status": "ok",
            },
        )

        append_jsonl(
            ledger_path,
            {
                "ts": utc_now_iso(),
                "event": "cycle_end",
                "cycle": cycle,
                "status": "ok",
            },
        )
        return 0

    except Exception as exc:  # Deliberate top-level containment for operational safety.
        append_jsonl(
            ledger_path,
            {
                "ts": utc_now_iso(),
                "event": "cycle_error",
                "cycle": cycle,
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        cp_safe_print(f"[ERROR] {type(exc).__name__}: {exc}")
        return 2


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ASO-X safe autopilot runner")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--once",
        action="store_true",
        help="Run exactly one cycle. This is the safe default.",
    )
    mode.add_argument(
        "--continuous",
        action="store_true",
        help="Run bounded continuous mode. Use with --max-cycles.",
    )

    parser.add_argument(
        "--max-cycles",
        type=int,
        default=None,
        help="Maximum number of cycles to run.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=5.0,
        help="Sleep duration between cycles.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate and log actions without executing side effects.",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER_PATH,
        help="Path to JSONL action ledger.",
    )
    parser.add_argument(
        "--kill-switch",
        type=Path,
        default=DEFAULT_KILL_SWITCH_PATH,
        help="Path to kill-switch file.",
    )

    args = parser.parse_args(argv)

    if args.max_cycles is not None and args.max_cycles < 1:
        parser.error("--max-cycles must be >= 1")

    if args.sleep_seconds < 0:
        parser.error("--sleep-seconds must be >= 0")

    return args


def resolve_max_cycles(args: argparse.Namespace) -> int:
    """
    Safety rule:
    - Default is exactly one cycle.
    - Continuous mode remains bounded.
    - If --continuous is used without --max-cycles, cap to 10.
    """
    if args.once or not args.continuous:
        return 1

    if args.max_cycles is not None:
        return args.max_cycles

    return 10



POLICY_DECISION_LOG = ".runtime/autopilot_policy_decisions.jsonl"


def _policy_append_jsonl_record(path: str, record: dict) -> None:
    import json
    from pathlib import Path

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")


def _policy_safe_str(value) -> str:
    if value is None:
        return ""
    return str(value)


def _policy_safe_float(value, default: float = 0.0) -> float:
    try:
        result = float(value)
    except Exception:
        return float(default)

    if result < 0.0:
        return 0.0
    if result > 1.0:
        return 1.0
    return result


def _policy_normalize_severity(value) -> str:
    raw = _policy_safe_str(value).strip().lower()

    if raw in {"critical", "crit", "sev0", "p0"}:
        return "critical"
    if raw in {"high", "sev1", "p1"}:
        return "high"
    if raw in {"medium", "med", "sev2", "p2"}:
        return "medium"
    if raw in {"low", "sev3", "p3"}:
        return "low"

    return "low"


def _policy_normalize_tags(value):
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        items = value
    else:
        items = str(value).split(",")

    out = []
    seen = set()

    for item in items:
        tag = str(item).strip().lower()
        if not tag:
            continue
        if tag in seen:
            continue
        seen.add(tag)
        out.append(tag)

    return out


def _policy_input_kwargs_from_signal(signal) -> dict:
    if isinstance(signal, dict):
        data = signal
    else:
        data = {}

    severity = _policy_normalize_severity(
        data.get("severity")
        or data.get("level")
        or data.get("priority")
        or "low"
    )

    confidence = _policy_safe_float(data.get("confidence", 0.0), default=0.0)
    tags = _policy_normalize_tags(data.get("tags"))

    subject = _policy_safe_str(
        data.get("subject")
        or data.get("service")
        or data.get("target")
        or data.get("component")
        or "autopilot"
    )

    source = _policy_safe_str(data.get("source") or "auto_pilot")
    signal_type = _policy_safe_str(data.get("signal_type") or data.get("type") or data.get("kind") or "runtime_signal")
    summary = _policy_safe_str(data.get("summary") or data.get("message") or data.get("reason") or "")

    return {
        "severity": severity,
        "confidence": confidence,
        "tags": tags,
        "subject": subject,
        "source": source,
        "signal_type": signal_type,
        "summary": summary,
        "message": summary,
        "reason": summary,
        "kind": signal_type,
        "type": signal_type,
        "component": subject,
    }


def _build_policy_input_from_signal(signal):
    import inspect

    source_kwargs = _policy_input_kwargs_from_signal(signal)

    try:
        sig = inspect.signature(PolicyInput)
    except Exception:
        return PolicyInput(**source_kwargs)

    kwargs = {}

    for name, param in sig.parameters.items():
        if name == "self":
            continue

        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue

        if name in source_kwargs:
            kwargs[name] = source_kwargs[name]
            continue

        if param.default is not inspect._empty:
            continue

        annotation_text = str(param.annotation).lower()

        if "float" in annotation_text:
            kwargs[name] = 0.0
        elif "int" in annotation_text:
            kwargs[name] = 0
        elif "bool" in annotation_text:
            kwargs[name] = False
        elif "list" in annotation_text or "set" in annotation_text or "tuple" in annotation_text:
            kwargs[name] = []
        elif name.endswith("s"):
            kwargs[name] = []
        else:
            kwargs[name] = ""

    return PolicyInput(**kwargs)


def _policy_action_value(action, *names, default=None):
    for name in names:
        if hasattr(action, name):
            return getattr(action, name)
        if isinstance(action, dict) and name in action:
            return action.get(name)

    return default


def _proposed_action_to_record(action) -> dict:
    payload = _policy_action_value(action, "payload", "metadata", "details", default={})

    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        payload = {"value": _policy_safe_str(payload)}

    return {
        "action_type": _policy_safe_str(
            _policy_action_value(action, "action_type", "type", "name", default="")
        ),
        "approval_required": bool(
            _policy_action_value(action, "approval_required", "requires_approval", default=False)
        ),
        "reason": _policy_safe_str(
            _policy_action_value(action, "reason", "summary", "message", default="")
        ),
        "payload": payload,
    }


def _decision_actions(decision):
    for name in ("proposed_actions", "actions", "recommended_actions"):
        value = getattr(decision, name, None)
        if value is not None:
            return list(value)

    if isinstance(decision, dict):
        for name in ("proposed_actions", "actions", "recommended_actions"):
            value = decision.get(name)
            if value is not None:
                return list(value)

    return []


def _policy_decision_to_record(signal, policy_input, decision) -> dict:
    proposed = _decision_actions(decision)
    input_kwargs = _policy_input_kwargs_from_signal(signal)

    return {
        "schema_version": 1,
        "component": "auto_pilot",
        "decision_engine": "tools.policy_matrix",
        "execution_mode": "review_only",
        "signal": signal if isinstance(signal, dict) else {"value": _policy_safe_str(signal)},
        "policy_input": {
            "severity": _policy_safe_str(getattr(policy_input, "severity", input_kwargs.get("severity", ""))),
            "confidence": float(getattr(policy_input, "confidence", input_kwargs.get("confidence", 0.0))),
            "tags": list(getattr(policy_input, "tags", input_kwargs.get("tags", [])) or []),
            "subject": _policy_safe_str(getattr(policy_input, "subject", input_kwargs.get("subject", ""))),
            "source": _policy_safe_str(getattr(policy_input, "source", input_kwargs.get("source", ""))),
            "signal_type": _policy_safe_str(getattr(policy_input, "signal_type", input_kwargs.get("signal_type", ""))),
            "summary": _policy_safe_str(getattr(policy_input, "summary", input_kwargs.get("summary", ""))),
        },
        "proposed_actions": [_proposed_action_to_record(a) for a in proposed],
        "approval_required": any(
            bool(_policy_action_value(a, "approval_required", "requires_approval", default=False))
            for a in proposed
        ),
    }


def evaluate_policy_for_signal(signal) -> dict:
    policy_input = _build_policy_input_from_signal(signal)
    decision = evaluate_policy_input(policy_input)
    record = _policy_decision_to_record(signal, policy_input, decision)
    _policy_append_jsonl_record(POLICY_DECISION_LOG, record)
    return record


def process_policy_signal(signal) -> dict:
    record = evaluate_policy_for_signal(signal)

    blocked = []
    review = []
    allowed = []

    for action in record.get("proposed_actions", []):
        if bool(action.get("approval_required", False)):
            review.append(action)
            continue

        action_type = str(action.get("action_type", "")).strip().lower()

        if action_type in {"create_alert", "emit_event", "log_only", "queue_operator_review"}:
            allowed.append(action)
            continue

        blocked.append(action)

    return {
        "execution_mode": "review_only",
        "review_actions": review,
        "allowed_actions": allowed,
        "blocked_actions": blocked,
        "decision_record": record,
    }


def _run_policy_matrix_smoke_from_env() -> int:
    import json
    import os

    sample_signal = {
        "severity": os.environ.get("AP_POLICY_SEVERITY", "high"),
        "confidence": os.environ.get("AP_POLICY_CONFIDENCE", "0.95"),
        "tags": os.environ.get("AP_POLICY_TAGS", "autopilot,review"),
        "subject": os.environ.get("AP_POLICY_SUBJECT", "autopilot"),
        "source": "auto_pilot",
        "signal_type": os.environ.get("AP_POLICY_SIGNAL_TYPE", "runtime_signal"),
        "summary": os.environ.get("AP_POLICY_SUMMARY", "manual policy integration smoke"),
    }

    result = process_policy_signal(sample_signal)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0

def main(argv: list[str] | None = None) -> int:

    import os

    if os.environ.get("AP_ENABLE_POLICY_MATRIX", "").strip().lower() in {"1", "true", "yes", "on"}:
        return _run_policy_matrix_smoke_from_env()

    args = parse_args(sys.argv[1:] if argv is None else argv)
    max_cycles = resolve_max_cycles(args)

    append_jsonl(
        args.ledger,
        {
            "ts": utc_now_iso(),
            "event": "autopilot_start",
            "dry_run": args.dry_run,
            "continuous": bool(args.continuous),
            "max_cycles": max_cycles,
            "kill_switch": str(args.kill_switch),
        },
    )

    exit_code = 0

    for cycle in range(1, max_cycles + 1):
        if kill_switch_active(args.kill_switch):
            append_jsonl(
                args.ledger,
                {
                    "ts": utc_now_iso(),
                    "event": "kill_switch_detected",
                    "cycle": cycle,
                    "path": str(args.kill_switch),
                    "status": "stopped",
                },
            )
            cp_safe_print("Autopilot stopped: kill switch detected.")
            return 10

        cycle_code = run_cycle(cycle=cycle, dry_run=args.dry_run, ledger_path=args.ledger)
        if cycle_code != 0:
            exit_code = cycle_code
            break

        if cycle < max_cycles:
            time.sleep(args.sleep_seconds)

    append_jsonl(
        args.ledger,
        {
            "ts": utc_now_iso(),
            "event": "autopilot_end",
            "status": "ok" if exit_code == 0 else "error",
            "exit_code": exit_code,
        },
    )

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
