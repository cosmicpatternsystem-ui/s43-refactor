import json
from pathlib import Path

import jsonschema
import pytest


SCHEMA_PATH = Path("repo/schemas/evidence_record.schema.json")


def load_schema():
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def valid_record():
    return {
        "schema_version": "1.0.0",
        "evidence_id": "evidence-2026-001",
        "retention": "3years",
        "subject": "AI Code Audit",
        "producer": "ASO-X-Autopilot",
        "decision_id": "dec-9999",
        "decision_category": "governance",
        "source_input_reference": "ref-1",
        "ai_output_reference": "ref-2",
        "governing_policy_refs": ["policy-triad-v1"],
        "operator_disposition": "accepted",
        "final_status": "accepted-for-promotion",
        "owner_role": "release-ops",
        "created_at_utc": "2026-07-15T00:00:00Z",
        "secret_handling": {
            "contains_secrets": False,
            "notes": "redacted",
        },
    }


def test_canonical_schema_disallows_extra_properties():
    schema = load_schema()
    assert schema.get("additionalProperties") is False


def test_canonical_schema_has_required_governance_fields():
    schema = load_schema()

    required_fields = {
        "schema_version",
        "evidence_id",
        "retention",
        "subject",
        "producer",
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
    }

    assert required_fields.issubset(set(schema["required"]))


def test_canonical_valid_record_passes_schema_validation():
    schema = load_schema()
    jsonschema.validate(instance=valid_record(), schema=schema)


def test_canonical_record_rejects_unexpected_properties():
    schema = load_schema()
    record = valid_record()
    record["unexpected_field"] = "not allowed"

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=record, schema=schema)


def test_canonical_record_rejects_legacy_evidence_pack_fields():
    schema = load_schema()
    record = valid_record()
    record["event_type"] = "legacy"
    record["payload_hash"] = "abc123"

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=record, schema=schema)