from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from durable_state import (
    REPO_ROOT,
    append_audit_event,
    append_change_ledger,
    initialize_schema,
    json_sha256,
    utc_now_iso,
)


AUDIT_JSON = REPO_ROOT / "runtime" / "audit" / "audit_log.json"


def load_audit_json() -> list[dict[str, Any]]:
    if not AUDIT_JSON.exists():
        raise FileNotFoundError(f"Audit JSON not found: {AUDIT_JSON}")

    with AUDIT_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        entries = data.get("entries")
        if isinstance(entries, list):
            return entries

    raise ValueError("Unsupported audit_log.json structure. Expected list or dict with entries list.")


def main() -> None:
    initialize_schema()

    entries = load_audit_json()
    source_hash = json_sha256(entries)

    append_change_ledger(
        event="AUDIT_JSON_READONLY_MIGRATION_STARTED",
        rule="Read-only migration. Source JSON must not be overwritten.",
        status="STARTED",
        payload={
            "source": "runtime/audit/audit_log.json",
            "source_entries": len(entries),
            "source_sha256": source_hash,
            "started_at": utc_now_iso(),
        },
    )

    inserted = 0

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            payload = {
                "legacy_index": index,
                "legacy_value": entry,
                "migration_note": "Non-dict audit entry preserved as payload.",
            }
            event = "LEGACY_AUDIT_ENTRY"
            status = "MIGRATED_NON_DICT"
        else:
            payload = {
                "legacy_index": index,
                "legacy_entry": entry,
            }
            event = str(entry.get("event", "LEGACY_AUDIT_ENTRY"))
            status = str(entry.get("status", "MIGRATED"))

        append_audit_event(
            event=event,
            status=status,
            source="runtime/audit/audit_log.json",
            payload=payload,
        )
        inserted += 1

    append_change_ledger(
        event="AUDIT_JSON_READONLY_MIGRATION_COMPLETED",
        rule="Read-only migration completed. Source JSON was not overwritten.",
        status="COMPLETED",
        payload={
            "source": "runtime/audit/audit_log.json",
            "source_entries": len(entries),
            "inserted_audit_events": inserted,
            "source_sha256": source_hash,
            "completed_at": utc_now_iso(),
        },
    )

    print("Audit JSON read-only migration completed.")
    print(f"Source: {AUDIT_JSON}")
    print(f"Source entries: {len(entries)}")
    print(f"Inserted audit_events: {inserted}")
    print(f"Source SHA256: {source_hash}")


if __name__ == "__main__":
    main()
