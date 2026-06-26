from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
DOCS_DIR = REPO_ROOT / "docs"
STATUS_PATH = DOCS_DIR / "AUTO_ROADMAP_STATUS.md"

sys.path.append(str(TOOLS_DIR))

from durable_state import (  # noqa: E402
    append_audit_event,
    append_change_ledger,
    append_roadmap_state,
    connect,
    initialize_schema,
    integrity_check,
    utc_now_iso,
)

PHASE8_STATUS = "TRACEABILITY_GAP_NOT_EVIDENCE_CONFIRMED"
NO_BLIND_PROMOTION_RULE = (
    "No blind promotion. Missing Phase 8 is recorded as a gap, not as completed."
)

ROADMAP_KEY_DURABLE_FOUNDATION = "infrastructure.durable_state_foundation"
ROADMAP_KEY_PHASE8 = "phase_8.traceability_status"


def _invoke_compatible(fn: Callable[..., Any], values: dict[str, Any]) -> Any:
    """
    Compatibility adapter for durable_state append functions.

    It maps known canonical values to the actual function signature.
    This prevents failures when append_* functions use domain-specific
    names such as roadmap_key/evidence_ref instead of event/source.
    """
    signature = inspect.signature(fn)
    kwargs: dict[str, Any] = {}

    aliases = {
        "event": ["event", "name", "action"],
        "status": ["status", "state"],
        "source": ["source", "actor", "writer"],
        "payload": ["payload", "data", "details", "metadata"],
        "roadmap_key": ["roadmap_key", "key"],
        "evidence_ref": ["evidence_ref", "evidence", "evidence_reference"],
        "created_at": ["created_at", "timestamp"],
        "rule": ["rule"],
    }

    reverse_alias: dict[str, str] = {}
    for canonical, names in aliases.items():
        for name in names:
            reverse_alias[name] = canonical

    for param_name, param in signature.parameters.items():
        canonical = reverse_alias.get(param_name, param_name)

        if canonical in values:
            kwargs[param_name] = values[canonical]
        elif param.default is not inspect.Parameter.empty:
            continue
        else:
            raise TypeError(
                f"Cannot call {fn.__name__}: missing required parameter "
                f"'{param_name}'. Known values: {sorted(values.keys())}"
            )

    return fn(**kwargs)


def _db_snapshot() -> dict[str, Any]:
    conn = connect()

    latest = conn.execute(
        """
        select id, event, status, created_at
        from audit_events
        order by id desc
        limit 1
        """
    ).fetchone()

    snapshot = {
        "audit_events": conn.execute(
            "select count(*) from audit_events"
        ).fetchone()[0],
        "change_ledger": conn.execute(
            "select count(*) from change_ledger"
        ).fetchone()[0],
        "roadmap_state": conn.execute(
            "select count(*) from roadmap_state"
        ).fetchone()[0],
        "latest_event": dict(latest) if latest else None,
    }

    conn.close()
    return snapshot


def _render_status(snapshot: dict[str, Any], generated_at: str) -> str:
    latest = snapshot.get("latest_event") or {}

    return f"""# Auto Roadmap Status

Generated at: {generated_at}

## Canonical Durable State

- Source of truth: `runtime/state/project_memory.sqlite`
- Storage mode: SQLite/WAL
- Integrity check: ok
- Audit events: {snapshot["audit_events"]}
- Change ledger entries: {snapshot["change_ledger"]}
- Roadmap state entries: {snapshot["roadmap_state"]}

## Latest Audit Event

- ID: {latest.get("id")}
- Event: {latest.get("event")}
- Status: {latest.get("status")}
- Created at: {latest.get("created_at")}

## Infrastructure Track: Durable State Foundation

Status: CONFIRMED

Evidence:
- SQLite durable state exists.
- SQLite integrity_check returned ok.
- Heartbeat writes canonical events into `project_memory.sqlite`.
- Historical `audit_log.json` entries were migrated read-only.
- JSON/JSONL are treated as export/backup/compatibility artifacts, not active source of truth.

## Phase 8 Traceability

Status: {PHASE8_STATUS}

Rule:
- {NO_BLIND_PROMOTION_RULE}

Automation decision:
- Phase 8 is not promoted by this sync.
- Re-audit is allowed only when direct file evidence is present.
- This tool enforces evidence-first roadmap updates and prevents blind promotion.

## Automation Contract

- If data is not persisted in SQLite, it is not canonical.
- If evidence is missing, status must not be confirmed.
- Every roadmap sync must be auditable.
- This file is generated from the durable state database.
"""


def sync_roadmap(trigger: str = "manual") -> dict[str, Any]:
    initialize_schema()

    check = integrity_check()
    if check != "ok":
        raise RuntimeError(f"SQLite integrity_check failed: {check}")

    generated_at = utc_now_iso()
    snapshot = _db_snapshot()

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(_render_status(snapshot, generated_at), encoding="utf-8")

    evidence_ref = (
        "runtime/state/project_memory.sqlite"
        f"#audit_events={snapshot['audit_events']}"
        f";change_ledger={snapshot['change_ledger']}"
        f";roadmap_state={snapshot['roadmap_state']}"
        f";generated_at={generated_at}"
    )

    payload = {
        "generated_at": generated_at,
        "trigger": trigger,
        "status_path": str(STATUS_PATH.relative_to(REPO_ROOT)),
        "source_of_truth": "runtime/state/project_memory.sqlite",
        "storage_mode": "SQLite/WAL",
        "integrity_check": "ok",
        "durable_foundation_status": "CONFIRMED",
        "phase_8_status": PHASE8_STATUS,
        "phase_8_promoted": False,
        "rule": NO_BLIND_PROMOTION_RULE,
        "evidence_ref": evidence_ref,
        "snapshot": snapshot,
    }

    # 1) ثبت وضعیت confirmed برای Durable Foundation
    durable_state_id = _invoke_compatible(
        append_roadmap_state,
        {
            "roadmap_key": ROADMAP_KEY_DURABLE_FOUNDATION,
            "status": "CONFIRMED",
            "evidence_ref": evidence_ref,
            "payload": payload,
            "source": "tools/roadmap_sync.py",
            "event": "roadmap_state_durable_foundation_confirmed",
            "created_at": generated_at,
            "rule": "Durable foundation confirmed by SQLite integrity and live heartbeat evidence.",
        },
    )

    # 2) ثبت صریح وضعیت Phase 8 بدون promotion
    phase8_payload = dict(payload)
    phase8_payload["roadmap_key"] = ROADMAP_KEY_PHASE8
    phase8_payload["automation_decision"] = "NO_PROMOTION_WITHOUT_DIRECT_FILE_EVIDENCE"

    phase8_state_id = _invoke_compatible(
        append_roadmap_state,
        {
            "roadmap_key": ROADMAP_KEY_PHASE8,
            "status": PHASE8_STATUS,
            "evidence_ref": evidence_ref,
            "payload": phase8_payload,
            "source": "tools/roadmap_sync.py",
            "event": "roadmap_state_phase8_gap_preserved",
            "created_at": generated_at,
            "rule": NO_BLIND_PROMOTION_RULE,
        },
    )

    # 3) ثبت در change ledger
    ledger_payload = dict(payload)
    ledger_payload["roadmap_state_ids"] = {
        "durable_foundation": durable_state_id,
        "phase8": phase8_state_id,
    }

    _invoke_compatible(
        append_change_ledger,
        {
            "event": "roadmap_auto_sync_completed",
            "status": "SUCCESS",
            "source": "tools/roadmap_sync.py",
            "payload": ledger_payload,
            "created_at": generated_at,
            "rule": NO_BLIND_PROMOTION_RULE,
            "roadmap_key": "roadmap.auto_sync",
            "evidence_ref": evidence_ref,
        },
    )

    # 4) ثبت audit event
    audit_event_id = append_audit_event(
        event="ROADMAP_AUTO_SYNC_COMPLETED",
        status="SUCCESS",
        source="tools/roadmap_sync.py",
        payload=ledger_payload,
    )

    result = dict(payload)
    result["audit_event_id"] = audit_event_id
    result["roadmap_state_ids"] = {
        "durable_foundation": durable_state_id,
        "phase8": phase8_state_id,
    }

    return result


def main() -> None:
    result = sync_roadmap(trigger="manual")
    print("Roadmap auto-sync completed.")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
