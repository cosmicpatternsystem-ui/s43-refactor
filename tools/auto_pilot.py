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
VALID_POLICY_MODES = frozenset({"off", "review", "enforce"})
DEFAULT_POLICY_MODE = "review"
ALLOWED_POLICY_ACTION_TYPES = frozenset(
    {
        "ignore",
        "log_observation",
        "queue_operator_review",
        "create_alert",
        "request_kill_switch_review",
    }
)


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



def _policy_safe_str(value: Any) -> str:
    if value is None:
        return "unknown"
    text = str(value).strip()
    return text if text else "unknown"


def _resolve_policy_mode() -> str:
    import os

    raw = os.environ.get("AP_POLICY_MODE", DEFAULT_POLICY_MODE)
    mode = raw.strip().lower()
    if mode not in VALID_POLICY_MODES:
        return DEFAULT_POLICY_MODE
    return mode



def _policy_decision_to_dict(decision: Any) -> dict[str, Any]:
    if isinstance(decision, dict):
        return decision

    if hasattr(decision, "model_dump"):
        dumped = decision.model_dump()
        if isinstance(dumped, dict):
            return dumped

    if hasattr(decision, "dict"):
        dumped = decision.dict()
        if isinstance(dumped, dict):
            return dumped

    if hasattr(decision, "__dict__"):
        dumped = {
            key: value
            for key, value in vars(decision).items()
            if not key.startswith("_")
        }
        if dumped:
            return dumped

    return {
        "status": "unknown",
        "decision_type": type(decision).__name__,
        "actions": [],
        "notes": "Policy decision object could not be fully serialized.",
    }

def process_policy_signal(signal: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate a policy signal using policy_matrix and apply local execution gating.

    Modes:
    - off: no policy enforcement, always allowed locally
    - review: evaluate and log, but do not hard-block execution
    - enforce: allow only a strict whitelist of action types
    """
    mode = _resolve_policy_mode()

    normalized_tags = signal.get("tags", [])
    if isinstance(normalized_tags, str):
        normalized_tags = [item.strip() for item in normalized_tags.split(",") if item.strip()]
    elif not isinstance(normalized_tags, list):
        normalized_tags = []

    try:
        policy_input = PolicyInput(
            severity=_policy_safe_str(signal.get("severity", "low")),
            confidence=float(signal.get("confidence", 0.0)),
            tags=normalized_tags,
            subject=_policy_safe_str(signal.get("subject", "autopilot")),
            source=_policy_safe_str(signal.get("source", "auto_pilot")),
            signal_type=_policy_safe_str(signal.get("signal_type", "runtime_signal")),
            summary=_policy_safe_str(signal.get("summary", "unknown")),
            requires_human_review=bool(signal.get("requires_human_review", False)),
        )

        matrix_decision = evaluate_policy_input(policy_input)
        matrix_result = _policy_decision_to_dict(matrix_decision)
        proposed_actions = matrix_result.get("actions", [])
        if not isinstance(proposed_actions, list):
            proposed_actions = []

        normalized_actions: list[dict[str, Any]] = []
        for action in proposed_actions:
            if isinstance(action, dict):
                normalized_actions.append(action)

        blocked_actions: list[dict[str, Any]] = []
        allowed_actions: list[dict[str, Any]] = []
        review_actions: list[dict[str, Any]] = []

        if mode == "off":
            allowed_actions = normalized_actions[:]
            decision_status = "allowed"
            reason_codes = ["policy_mode_off"]
            decision_notes = "Policy enforcement disabled by AP_POLICY_MODE=off."

        elif mode == "review":
            allowed_actions = normalized_actions[:]
            review_actions = [
                action
                for action in normalized_actions
                if _policy_safe_str(action.get("type")) not in ALLOWED_POLICY_ACTION_TYPES
            ]
            decision_status = "review"
            reason_codes = ["policy_mode_review"]
            decision_notes = "Policy evaluated in review mode; no hard block applied."

        else:
            signal_action_type_raw = signal.get("type")
            signal_action_type = (
                _policy_safe_str(signal_action_type_raw)
                if signal_action_type_raw is not None
                else ""
            )
            signal_confidence = float(signal.get("confidence", 0.0))

            signal_invalid_for_enforce = (
                (signal_action_type and signal_action_type not in ALLOWED_POLICY_ACTION_TYPES)
                or signal_confidence <= 0.0
            )

            for action in normalized_actions:
                action_type = _policy_safe_str(action.get("type"))
                if action_type in ALLOWED_POLICY_ACTION_TYPES:
                    allowed_actions.append(action)
                else:
                    review_actions.append(action)

            if signal_invalid_for_enforce:
                blocked_actions = [
                    {
                        "type": signal_action_type or "invalid_signal",
                        "detail": "Signal failed local enforce validation.",
                    }
                ]
                decision_status = "blocked"
                reason_codes = ["enforce_blocked_invalid_signal"]
                decision_notes = "Signal failed local enforce validation."
            else:
                decision_status = "allowed"
                reason_codes = ["enforce_allowed_with_policy_review_actions"]
                decision_notes = "Signal passed enforce validation; non-whitelisted policy actions were retained for review."

        return {
            "schema_version": 2,
            "execution_mode": mode,
            "decision_status": decision_status,
            "reason_codes": reason_codes,
            "decision_notes": decision_notes,
            "allowed_actions": allowed_actions,
            "blocked_actions": blocked_actions,
            "review_actions": review_actions,
            "policy_actions": normalized_actions,
            "policy_result": matrix_result,
        }

    except Exception as exc:
        return {
            "schema_version": 2,
            "execution_mode": mode,
            "decision_status": "blocked",
            "reason_codes": ["policy_engine_exception_fail_safe"],
            "decision_notes": f"Policy processing failed closed: {type(exc).__name__}: {exc}",
            "allowed_actions": [],
            "blocked_actions": [
                {
                    "type": "internal_error",
                    "detail": type(exc).__name__,
                }
            ],
            "review_actions": [],
            "policy_actions": [],
            "policy_result": {
                "status": "error",
                "error": type(exc).__name__,
                "message": str(exc),
            },
        }

def run_cycle(*, cycle: int, dry_run: bool, ledger_path: Path) -> int:
    append_jsonl(
        ledger_path,
        {
            "ts": utc_now_iso(),
            "event": "cycle_start",
            "cycle": cycle,
            "dry_run": dry_run,
            "status": "started",
        },
    )

    try:
        guardian_report = check_guardian_reports()
        policy_result = apply_policy_rules(guardian_report)
        policy_mode = _resolve_policy_mode()

        policy_signal = {
            "severity": "low",
            "confidence": 1.0 if bool(policy_result.get("allowed")) else 0.6,
            "tags": ["unsafe_execution"] if not bool(policy_result.get("allowed")) else [],
            "subject": "autopilot",
            "source": "auto_pilot",
            "signal_type": "guardian_report",
            "summary": _policy_safe_str(policy_result.get("status", "unknown")),
            "requires_human_review": not bool(policy_result.get("allowed")),
        }
        policy_gate = process_policy_signal(policy_signal)

        if policy_mode == "enforce" and policy_gate.get("decision_status") != "allowed":
            append_jsonl(
                ledger_path,
                {
                    "ts": utc_now_iso(),
                    "event": "policy_blocked",
                    "cycle": cycle,
                    "policy_mode": policy_mode,
                    "policy_decision_status": policy_gate.get("decision_status"),
                    "reason_codes": policy_gate.get("reason_codes", []),
                    "decision_notes": policy_gate.get("decision_notes", ""),
                    "blocked_actions": policy_gate.get("blocked_actions", []),
                    "review_actions": policy_gate.get("review_actions", []),
                    "status": "blocked",
                },
            )
            return 12

        if dry_run:
            action = "dry_run_noop"
        else:
            action = "noop"

        append_jsonl(
            ledger_path,
            {
                "ts": utc_now_iso(),
                "event": "cycle_completed",
                "cycle": cycle,
                "dry_run": dry_run,
                "action": action,
                "guardian_status": guardian_report.get("status"),
                "policy_status": policy_result.get("status"),
                "policy_allowed": policy_result.get("allowed"),
                "policy_mode": policy_mode,
                "policy_decision_status": policy_gate.get("decision_status"),
                "policy_reason_codes": policy_gate.get("reason_codes", []),
                "policy_decision_notes": policy_gate.get("decision_notes", ""),
                "status": "ok",
            },
        )
        return 0

    except Exception as exc:
        append_jsonl(
            ledger_path,
            {
                "ts": utc_now_iso(),
                "event": "cycle_failed",
                "cycle": cycle,
                "error": type(exc).__name__,
                "message": str(exc),
                "status": "error",
            },
        )
        cp_safe_print("Autopilot cycle failed: " + str(exc))
        return 1

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


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ASO-X Auto Pilot")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute in dry-run mode without external side effects.",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run multiple cycles instead of a single cycle.",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=1,
        help="Maximum number of cycles to execute when running continuously.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=5.0,
        help="Sleep duration between cycles in continuous mode.",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER_PATH,
        help="Path to the JSONL action ledger.",
    )
    parser.add_argument(
        "--kill-switch",
        type=Path,
        default=DEFAULT_KILL_SWITCH_PATH,
        help="Path to the kill switch file.",
    )
    return parser.parse_args(argv)


def resolve_max_cycles(args: argparse.Namespace) -> int:
    if args.continuous:
        if args.max_cycles < 1:
            raise ValueError("--max-cycles must be >= 1 when --continuous is set")
        return args.max_cycles
    return 1


def main(argv: list[str] | None = None) -> int:

    import os

    if os.environ.get("AP_ENABLE_POLICY_MATRIX", "").strip().lower() in {"1", "true", "yes", "on"}:
        return _run_policy_matrix_smoke_from_env()

    args = parse_args(sys.argv[1:] if argv is None else argv)

    try:
        max_cycles = resolve_max_cycles(args)
    except ValueError as exc:
        cp_safe_print("Argument error: " + str(exc))
        return 2

    append_jsonl(
        args.ledger,
        {
            "ts": utc_now_iso(),
            "event": "autopilot_start",
            "dry_run": args.dry_run,
            "continuous": bool(args.continuous),
            "max_cycles": max_cycles,
            "kill_switch": str(args.kill_switch),
            "policy_mode": _resolve_policy_mode(),
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
            "event": "autopilot_stop",
            "status": "completed" if exit_code == 0 else "stopped",
            "exit_code": exit_code,
        },
    )

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
