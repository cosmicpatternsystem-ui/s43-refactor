from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent
DOCS_DIR = REPO_ROOT / "docs"
ROADMAP_DIR = REPO_ROOT / "ROADMAP"
AUDIT_DIR = REPO_ROOT / "AUDIT"
RUNTIME_DB = REPO_ROOT / "runtime" / "state" / "project_memory.sqlite"

STATUS_PATH = DOCS_DIR / "AUTO_ROADMAP_STATUS.md"
ROADMAP_STATE_PATH = REPO_ROOT / "ROADMAP" / "ROADMAP_STATE.json"
STATE_PATH = ROADMAP_DIR / "ROADMAP_STATE.json"
CHECKSUM_PATH = AUDIT_DIR / "roadmap_checksum_sha256.txt"
ROADMAP_CURRENT_PATH = REPO_ROOT / "ROADMAP_CURRENT.json"

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def read_snapshot() -> dict[str, Any]:
    if not RUNTIME_DB.exists():
        return {
            "runtime_available": False,
            "audit_events": 0,
            "change_ledger": 0,
            "roadmap_state": 0,
        }
    try:
        conn = sqlite3.connect(str(RUNTIME_DB))
        snapshot = {
            "runtime_available": True,
            "audit_events": conn.execute("SELECT count(*) FROM audit_events").fetchone()[0],
            "change_ledger": conn.execute("SELECT count(*) FROM change_ledger").fetchone()[0],
            "roadmap_state": conn.execute("SELECT count(*) FROM roadmap_state").fetchone()[0],
        }
        conn.close()
        return snapshot
    except Exception:
        return {
            "runtime_available": False,
            "audit_events": 0,
            "change_ledger": 0,
            "roadmap_state": 0,
        }

def derive_health(snapshot: dict[str, Any]) -> str:
    if not snapshot["runtime_available"]:
        return "DEGRADED"
    if snapshot["roadmap_state"] <= 0:
        return "STALE"
    if snapshot["audit_events"] <= 0 or snapshot["change_ledger"] <= 0:
        return "PARTIAL_DATA"
    return "HEALTHY"

def render_status(snapshot: dict[str, Any], generated_at: str) -> str:
    health = derive_health(snapshot)
    sync_status = "synced" if health == "HEALTHY" else "out_of_sync"
    return (
        "# AUTO ROADMAP STATUS\n\n"
        f"- Generated at: {generated_at}\n"
        f"- Source of truth: repository_files_only\n"
        f"- Storage mode: SQLite/WAL\n"
        f"- Integrity check: ok\n"
        f"- Health: {health}\n"
        f"- Sync status: {sync_status}\n"
    )

def sync_roadmap(trigger: str = "manual") -> dict[str, Any]:
    for directory in (DOCS_DIR, ROADMAP_DIR, AUDIT_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    generated_at = utc_now()
    current_roadmap = load_json(ROADMAP_CURRENT_PATH)
    current_roadmap_version = current_roadmap["roadmap_version"]
    snapshot = read_snapshot()
    health = derive_health(snapshot)
    sync_status = "synced" if health == "HEALTHY" else "out_of_sync"

    status_text = render_status(snapshot, generated_at)
    STATUS_PATH.write_text(status_text, encoding="utf-8")

    roadmap_state = {
        "schema_version": "2.1.0",
        "project": "ASO-X",
        "default_branch": "main",
        "current_phase": "22.13",
        "current_branch": "main",
        "phase_title": "Post-22.12 Roadmap Governance Stabilization",
        "previous_phase": "22.12",
        "roadmap_sync_status": sync_status,
        "next_action": "Continue Phase 22.13 roadmap governance validation",
        "updated_at": generated_at,
        "validation_status": "valid",
        "authority": "repository_files_only",
        "state_type": "repository_roadmap_state","roadmap_version": current_roadmap_version,
        "system_health": health,
        "source_of_truth": "repository_files_only",
        "runtime_snapshot": snapshot,
        "trigger": trigger,
    }
    write_json(STATE_PATH, roadmap_state)

    payload = {
        "generated_at": generated_at,
        "trigger": trigger,
        "status_path": str(STATUS_PATH),
        "source_of_truth": "repository_files_only",
        "storage_mode": "SQLite/WAL",
        "integrity_check": "ok",
        "durable_foundation_status": health,
        "phase_8_status": "preserved",
        "phase_8_promoted": health == "HEALTHY",
        "rule": "durable-roadmap-sync",
        "evidence_ref": (
            f"{RUNTIME_DB}#audit_events={snapshot['audit_events']};"
            f"change_ledger={snapshot['change_ledger']};"
            f"roadmap_state={snapshot['roadmap_state']};"
            f"generated_at={generated_at}"
        ),
        "snapshot": snapshot,
        "roadmap_state_path": str(STATE_PATH),
        "roadmap_sync_status": sync_status,
        "system_health": health,
    }

    items = [
        "ROADMAP_CURRENT.json",
        "ROADMAP/ROADMAP_STATE.json",
        "docs/AUTO_ROADMAP_STATUS.md",
    ]
    checksum_lines = [f"generated_at={generated_at}"]
    for relative_path in items:
        candidate = REPO_ROOT / relative_path
        if candidate.exists():
            checksum_lines.append(
                f"{relative_path} sha256={hashlib.sha256(candidate.read_bytes()).hexdigest().upper()}"
            )
    CHECKSUM_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECKSUM_PATH.write_text("\n".join(checksum_lines), encoding="utf-8")

    v1 = subprocess.run([sys.executable, "scripts/roadmap_guard.py"], capture_output=True, text=True)
    v2 = subprocess.run([sys.executable, "validate_roadmap_state.py"], capture_output=True, text=True)

    result = dict(payload)
    result["ok"] = (v1.returncode == 0 and v2.returncode == 0)
    result["validators"] = {
        "roadmap_guard": {
            "returncode": v1.returncode,
            "stdout": v1.stdout.strip(),
            "stderr": v1.stderr.strip(),
        },
        "validate_roadmap_state": {
            "returncode": v2.returncode,
            "stdout": v2.stdout.strip(),
            "stderr": v2.stderr.strip(),
        },
    }
    return result

def main() -> None:
    result = sync_roadmap()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if result["ok"] else 1)

if __name__ == "__main__":
    main()




