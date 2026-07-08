from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from durable_state import DB_PATH, append_audit_event, initialize_schema, integrity_check, utc_now_iso


def run_check() -> int:
    if not DB_PATH.exists():
        print(f"Heartbeat check failed. Durable state database not found: {DB_PATH}")
        return 2

    check = integrity_check()
    if check != "ok":
        print(f"CRITICAL ERROR: SQLite integrity check failed: {check}")
        return 1

    print("Heartbeat check successful. SQLite integrity_check: ok")
    return 0


def run_pulse() -> int:
    initialize_schema()

    check = integrity_check()
    if check != "ok":
        print(f"CRITICAL ERROR: SQLite integrity check failed: {check}")
        return 1

    event_id = append_audit_event(
        event="GOLD_HEARTBEAT_PULSE",
        status="SUCCESS_DURABLE",
        source="tools/heartbeat.py",
        payload={
            "timestamp": utc_now_iso(),
            "engine": "ASO-X Durable Core v1.1.0",
            "storage_mode": "SQLite/WAL",
            "integrity_verified": True,
        },
    )

    print(f"Heartbeat pulse successful. Event ID: {event_id} (Stored in project_memory.sqlite)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ASO-X durable heartbeat utility."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run a read-oriented SQLite integrity check without appending a heartbeat event.",
    )
    parser.add_argument(
        "--pulse",
        action="store_true",
        help="Append a heartbeat event to the durable SQLite state. This is the default action.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.check:
        return run_check()

    return run_pulse()


if __name__ == "__main__":
    raise SystemExit(main())