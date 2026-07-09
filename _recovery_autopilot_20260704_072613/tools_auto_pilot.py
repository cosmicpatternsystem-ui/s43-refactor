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


def main(argv: list[str] | None = None) -> int:
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
