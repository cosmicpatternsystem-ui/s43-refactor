from __future__ import annotations

import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = REPO_ROOT / "runtime" / "state"
DB_PATH = STATE_DIR / "project_memory.sqlite"


SCHEMA_VERSION = 1


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def json_sha256(value: Any) -> str:
    return sha256_text(canonical_json(value))


def connect() -> sqlite3.Connection:
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=FULL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA busy_timeout=5000;")

    return conn


def initialize_schema() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL,
                description TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                event TEXT NOT NULL,
                status TEXT,
                source TEXT,
                payload_json TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS change_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                event TEXT NOT NULL,
                rule TEXT,
                status TEXT,
                payload_json TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS roadmap_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                roadmap_key TEXT NOT NULL,
                status TEXT NOT NULL,
                evidence_ref TEXT,
                payload_json TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ai_pattern_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                category TEXT NOT NULL,
                subject TEXT,
                payload_json TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_audit_events_created_at
                ON audit_events(created_at);

            CREATE INDEX IF NOT EXISTS idx_audit_events_event
                ON audit_events(event);

            CREATE INDEX IF NOT EXISTS idx_change_ledger_created_at
                ON change_ledger(created_at);

            CREATE INDEX IF NOT EXISTS idx_roadmap_state_key
                ON roadmap_state(roadmap_key);

            CREATE INDEX IF NOT EXISTS idx_ai_pattern_category
                ON ai_pattern_records(category);
            """
        )

        existing = conn.execute(
            "SELECT version FROM schema_migrations WHERE version = ?",
            (SCHEMA_VERSION,),
        ).fetchone()

        if existing is None:
            conn.execute(
                """
                INSERT INTO schema_migrations(version, applied_at, description)
                VALUES (?, ?, ?)
                """,
                (
                    SCHEMA_VERSION,
                    utc_now_iso(),
                    "Initial durable state schema: audit, ledger, roadmap, AI pattern records.",
                ),
            )


def append_audit_event(
    event: str,
    status: Optional[str] = None,
    source: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
) -> int:
    payload = payload or {}
    payload_json = canonical_json(payload)
    payload_hash = sha256_text(payload_json)

    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO audit_events(
                created_at,
                event,
                status,
                source,
                payload_json,
                payload_sha256
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                utc_now_iso(),
                event,
                status,
                source,
                payload_json,
                payload_hash,
            ),
        )
        return int(cur.lastrowid)


def append_change_ledger(
    event: str,
    rule: Optional[str],
    status: Optional[str],
    payload: dict[str, Any],
) -> int:
    payload_json = canonical_json(payload)
    payload_hash = sha256_text(payload_json)

    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO change_ledger(
                created_at,
                event,
                rule,
                status,
                payload_json,
                payload_sha256
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                utc_now_iso(),
                event,
                rule,
                status,
                payload_json,
                payload_hash,
            ),
        )
        return int(cur.lastrowid)


def append_roadmap_state(
    roadmap_key: str,
    status: str,
    evidence_ref: Optional[str],
    payload: dict[str, Any],
) -> int:
    payload_json = canonical_json(payload)
    payload_hash = sha256_text(payload_json)

    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO roadmap_state(
                created_at,
                roadmap_key,
                status,
                evidence_ref,
                payload_json,
                payload_sha256
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                utc_now_iso(),
                roadmap_key,
                status,
                evidence_ref,
                payload_json,
                payload_hash,
            ),
        )
        return int(cur.lastrowid)


def append_ai_pattern_record(
    category: str,
    subject: Optional[str],
    payload: dict[str, Any],
) -> int:
    payload_json = canonical_json(payload)
    payload_hash = sha256_text(payload_json)

    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO ai_pattern_records(
                created_at,
                category,
                subject,
                payload_json,
                payload_sha256
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                utc_now_iso(),
                category,
                subject,
                payload_json,
                payload_hash,
            ),
        )
        return int(cur.lastrowid)


def integrity_check() -> str:
    with connect() as conn:
        row = conn.execute("PRAGMA integrity_check;").fetchone()
        return str(row[0])


def bootstrap() -> None:
    initialize_schema()

    append_change_ledger(
        event="DURABLE_STATE_FOUNDATION_BOOTSTRAPPED",
        rule="No blind promotion. No critical state without durable persistence.",
        status="INITIALIZED",
        payload={
            "canonical_target": "runtime/state/project_memory.sqlite",
            "journal_mode": "WAL",
            "synchronous": "FULL",
            "foreign_keys": True,
            "schema_version": SCHEMA_VERSION,
            "phase8_status": "TRACEABILITY_GAP_NOT_EVIDENCE_CONFIRMED",
        },
    )

    append_roadmap_state(
        roadmap_key="infrastructure.durable_state_foundation",
        status="APPROVED_INITIALIZED",
        evidence_ref="CHANGE_CONTROL_LEDGER.jsonl / PHASE_TRACEABILITY_EVIDENCE.json",
        payload={
            "decision": "Migrate canonical durable state to SQLite/WAL.",
            "canonical_state": "runtime/state/project_memory.sqlite",
            "legacy_json_role": "export_backup_compatibility_only",
            "critical_json_overwrite": "forbidden",
            "phase8_status": "TRACEABILITY_GAP_NOT_EVIDENCE_CONFIRMED",
            "no_blind_promotion": True,
        },
    )


if __name__ == "__main__":
    bootstrap()
    result = integrity_check()
    print(f"Durable state initialized: {DB_PATH}")
    print(f"SQLite integrity_check: {result}")
