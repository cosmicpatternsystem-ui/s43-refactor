from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Make repo-root imports work when running this file directly.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from asoctl import ASOControl, write_json_atomic


DEFAULT_EVIDENCE_RECORD_PATH = Path("artifacts/evidence/record.json")
DEFAULT_PAYLOAD_ARCHIVE_DIR = Path("artifacts/evidence/raw")


def utc_now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sanitize_component(value: str) -> str:
    cleaned: list[str] = []
    for ch in value.strip():
        if ch.isalnum() or ch in ("-", "_", "."):
            cleaned.append(ch)
        else:
            cleaned.append("-")
    collapsed = "".join(cleaned).strip("-")
    return collapsed or "unspecified"


def archive_payload(
    payload: Any,
    evidence_id: str,
    archive_dir: Path = DEFAULT_PAYLOAD_ARCHIVE_DIR,
) -> Path:
    archive_dir.mkdir(parents=True, exist_ok=True)
    payload_name = f"{sanitize_component(evidence_id)}.payload.json"
    payload_path = archive_dir / payload_name
    write_json_atomic(payload_path, payload)
    return payload_path


def build_evidence_record(
    *,
    evidence_id: str,
    producer: str,
    subject: str,
    payload_path: Path,
    retention: str = "50y",
    decision_id: str | None = None,
    decision_category: str = "governance",
    ai_output_reference: str = "none",
    operator_disposition: str = "accepted",
    final_status: str = "accepted-for-review",
    owner_role: str = "governance-maintainer",
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "evidence_id": evidence_id,
        "producer": producer,
        "subject": subject,
        "retention": retention,
        "decision_id": decision_id or f"decision-{sanitize_component(evidence_id)}",
        "decision_category": decision_category,
        "source_input_reference": payload_path.as_posix(),
        "ai_output_reference": ai_output_reference,
        "governing_policy_refs": [
            "repo/schemas/evidence_record.schema.json",
            "repo/schemas/evidence_ledger_entry.schema.json",
        ],
        "operator_disposition": operator_disposition,
        "final_status": final_status,
        "owner_role": owner_role,
        "created_at_utc": utc_now_z(),
        "secret_handling": {
            "contains_secrets": False,
            "notes": "No secrets intentionally included in this MCP-01 record.",
        },
    }


def ingest_evidence(
    *,
    payload: Any,
    evidence_id: str,
    producer: str,
    subject: str,
    retention: str = "50y",
    record_path: Path = DEFAULT_EVIDENCE_RECORD_PATH,
) -> dict[str, Any]:
    payload_path = archive_payload(payload=payload, evidence_id=evidence_id)

    record = build_evidence_record(
        evidence_id=evidence_id,
        producer=producer,
        subject=subject,
        payload_path=payload_path,
        retention=retention,
    )

    write_json_atomic(record_path, record)

    ctl = ASOControl()

    validate_rc = ctl.evidence_validate(record_path)
    if validate_rc != 0:
        return {
            "decision": "fail",
            "stage": "validate",
            "record_path": record_path.as_posix(),
            "payload_path": payload_path.as_posix(),
            "return_code": validate_rc,
        }

    ledger_rc = ctl.evidence_ledger_record(record_path)
    if ledger_rc != 0:
        return {
            "decision": "fail",
            "stage": "ledger-record",
            "record_path": record_path.as_posix(),
            "payload_path": payload_path.as_posix(),
            "return_code": ledger_rc,
        }

    return {
        "decision": "pass",
        "stage": "complete",
        "record_path": record_path.as_posix(),
        "payload_path": payload_path.as_posix(),
        "evidence_id": evidence_id,
        "producer": producer,
        "subject": subject,
        "retention": retention,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="src/evidence/ingest/ingestor.py",
        description="MCP-01 evidence ingestion adapter for ASO-X",
    )
    parser.add_argument("--payload-file", type=Path, required=True, help="Path to input JSON payload")
    parser.add_argument("--evidence-id", required=True, help="Stable evidence identifier")
    parser.add_argument("--producer", default="mcp-ingestor", help="Evidence producer")
    parser.add_argument("--subject", default="ASO-X", help="Evidence subject")
    parser.add_argument("--retention", default="50y", help="Retention class/policy")
    parser.add_argument(
        "--record-path",
        type=Path,
        default=DEFAULT_EVIDENCE_RECORD_PATH,
        help="Destination evidence record path",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload = json.loads(args.payload_file.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(json.dumps({
            "decision": "error",
            "reason": f"payload file not found: {args.payload_file.as_posix()}",
        }, ensure_ascii=True, sort_keys=True, indent=2))
        return 2
    except json.JSONDecodeError as exc:
        print(json.dumps({
            "decision": "fail",
            "reason": f"invalid JSON payload: {exc}",
            "payload_file": args.payload_file.as_posix(),
        }, ensure_ascii=True, sort_keys=True, indent=2))
        return 1

    result = ingest_evidence(
        payload=payload,
        evidence_id=args.evidence_id,
        producer=args.producer,
        subject=args.subject,
        retention=args.retention,
        record_path=args.record_path,
    )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    return 0 if result.get("decision") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
