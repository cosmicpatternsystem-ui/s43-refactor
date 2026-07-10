from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "schema_version",
    "evidence_id",
    "decision_id",
    "decision_category",
    "source_input_reference",
    "ai_output_reference",
    "governing_policy_refs",
    "operator_disposition",
    "final_status",
    "owner_role",
    "created_at_utc",
    "secret_handling",
    "producer",
    "subject",
    "retention",
]

OPTIONAL = {
    "supporting_context",
    "limitations_or_uncertainty",
    "evidence_refs",
    "reviewed_at_utc",
}

DECISION_CATEGORIES = {
    "governance",
    "safe-merge",
    "release-readiness",
    "roadmap",
    "audit",
    "ai-assisted-decision",
    "operational",
}

OPERATOR_DISPOSITIONS = {
    "accepted",
    "accepted-with-limits",
    "rejected",
    "blocked",
    "deferred",
    "advisory-only",
}

FINAL_STATUSES = {
    "accepted-for-promotion",
    "accepted-for-review",
    "advisory-only",
    "blocked",
    "rejected",
    "invalid",
    "deferred-for-review",
}

EVIDENCE_KINDS = {
    "source-input",
    "ai-output",
    "policy",
    "contract",
    "audit",
    "roadmap",
    "artifact",
    "review",
    "other",
}

REDACTION_STATUSES = {
    "not-required",
    "redacted-reference-only",
}

SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
EVIDENCE_ID_RE = re.compile(r"^evidence-[A-Za-z0-9._-]+$")

def fail(path: Path, message: str) -> None:
    raise ValueError(f"{path.as_posix()}: {message}")

def require_string(path: Path, data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(path, f"{key} must be a non-empty string")
    return value

def parse_utc(path: Path, value: str, key: str) -> None:
    candidate = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        fail(path, f"{key} must be an ISO-8601 UTC timestamp")
    if parsed.tzinfo is None:
        fail(path, f"{key} must include UTC timezone")
    if parsed.astimezone(timezone.utc).utcoffset().total_seconds() != 0:
        fail(path, f"{key} must be UTC")

def validate_record(path: Path) -> None:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        fail(path, "record must be a JSON object")

    allowed = set(REQUIRED) | OPTIONAL
    extra = sorted(set(data) - allowed)
    if extra:
        fail(path, "unexpected properties: " + ", ".join(extra))

    missing = [key for key in REQUIRED if key not in data]
    if missing:
        fail(path, "missing required properties: " + ", ".join(missing))

    if data["schema_version"] != "1.0.0":
        fail(path, "schema_version must be 1.0.0")

    evidence_id = require_string(path, data, "evidence_id")
    if not EVIDENCE_ID_RE.fullmatch(evidence_id):
        fail(path, "evidence_id must match ^evidence-[A-Za-z0-9._-]+$")

    require_string(path, data, "producer")
    require_string(path, data, "subject")

    retention = data.get("retention")
    if isinstance(retention, str):
        if not retention.strip():
            fail(path, "retention must be a non-empty string")
    elif isinstance(retention, dict):
        if not retention:
            fail(path, "retention must not be an empty object")
        extra_retention = sorted(set(retention) - {"class", "policy"})
        if extra_retention:
            fail(path, "retention unexpected properties: " + ", ".join(extra_retention))
        retention_class = retention.get("class")
        retention_policy = retention.get("policy")
        if retention_class is None and retention_policy is None:
            fail(path, "retention object must contain class or policy")
        if retention_class is not None and (not isinstance(retention_class, str) or not retention_class.strip()):
            fail(path, "retention.class must be a non-empty string")
        if retention_policy is not None and (not isinstance(retention_policy, str) or not retention_policy.strip()):
            fail(path, "retention.policy must be a non-empty string")
    else:
        fail(path, "retention must be a non-empty string or object")

    require_string(path, data, "decision_id")
    require_string(path, data, "source_input_reference")
    require_string(path, data, "ai_output_reference")
    require_string(path, data, "owner_role")

    if data["decision_category"] not in DECISION_CATEGORIES:
        fail(path, "decision_category is not allowed")

    if data["operator_disposition"] not in OPERATOR_DISPOSITIONS:
        fail(path, "operator_disposition is not allowed")

    if data["final_status"] not in FINAL_STATUSES:
        fail(path, "final_status is not allowed")

    refs = data["governing_policy_refs"]
    if not isinstance(refs, list) or not refs:
        fail(path, "governing_policy_refs must be a non-empty array")
    for index, item in enumerate(refs):
        if not isinstance(item, str) or not item.strip():
            fail(path, f"governing_policy_refs[{index}] must be a non-empty string")

    parse_utc(path, require_string(path, data, "created_at_utc"), "created_at_utc")

    if "reviewed_at_utc" in data:
        parse_utc(path, require_string(path, data, "reviewed_at_utc"), "reviewed_at_utc")

    if "supporting_context" in data and not isinstance(data["supporting_context"], str):
        fail(path, "supporting_context must be a string")

    if "limitations_or_uncertainty" in data and not isinstance(data["limitations_or_uncertainty"], str):
        fail(path, "limitations_or_uncertainty must be a string")

    if "evidence_refs" in data:
        evidence_refs = data["evidence_refs"]
        if not isinstance(evidence_refs, list):
            fail(path, "evidence_refs must be an array")
        for index, ref in enumerate(evidence_refs):
            if not isinstance(ref, dict):
                fail(path, f"evidence_refs[{index}] must be an object")
            allowed_ref_keys = {"label", "path_or_uri", "kind", "sha256"}
            extra_ref = sorted(set(ref) - allowed_ref_keys)
            if extra_ref:
                fail(path, f"evidence_refs[{index}] unexpected properties: " + ", ".join(extra_ref))
            for key in ["label", "path_or_uri", "kind"]:
                if key not in ref or not isinstance(ref[key], str) or not ref[key].strip():
                    fail(path, f"evidence_refs[{index}].{key} must be a non-empty string")
            if ref["kind"] not in EVIDENCE_KINDS:
                fail(path, f"evidence_refs[{index}].kind is not allowed")
            if "sha256" in ref and (not isinstance(ref["sha256"], str) or not SHA256_RE.fullmatch(ref["sha256"])):
                fail(path, f"evidence_refs[{index}].sha256 must be 64 hex characters")

    secret_handling = data["secret_handling"]
    if not isinstance(secret_handling, dict):
        fail(path, "secret_handling must be an object")

    allowed_secret_keys = {"contains_secrets", "redaction_status", "notes"}
    extra_secret = sorted(set(secret_handling) - allowed_secret_keys)
    if extra_secret:
        fail(path, "secret_handling unexpected properties: " + ", ".join(extra_secret))

    if secret_handling.get("contains_secrets") is not False:
        fail(path, "secret_handling.contains_secrets must be false")

    if secret_handling.get("redaction_status") not in REDACTION_STATUSES:
        fail(path, "secret_handling.redaction_status is not allowed")

    if "notes" in secret_handling and not isinstance(secret_handling["notes"], str):
        fail(path, "secret_handling.notes must be a string")

def discover(paths: list[str]) -> list[Path]:
    if paths:
        return [Path(item).resolve() for item in paths]
    candidates: list[Path] = []
    candidates.extend((ROOT / "artifacts" / "examples").glob("evidence_record*.json"))
    candidates.extend((ROOT / "artifacts" / "evidence").glob("*.json"))
    return sorted(set(candidates))

def main(argv: list[str]) -> int:
    records = discover(argv)
    if not records:
        print("no evidence records found")
        return 0
    for record in records:
        validate_record(record)
        print(f"valid {record.relative_to(ROOT).as_posix()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
