import json
import jsonschema
import pytest

SCHEMA_PATH = "evidence_pack/schemas/evidence-record.schema.json"


def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_evidence_schema_alignment():
    """Verify that schema uses event_type and payload_hash."""
    schema = load_schema()

    assert "event_type" in schema["required"]
    assert "payload_hash" in schema["required"]
    assert "evidence_type" not in schema["properties"]
    assert "content_hash" not in schema["properties"]
    assert schema["properties"]["payload_hash"]["pattern"] == r"^sha256:[0-9a-f]{64}$"


def test_valid_record_against_schema():
    schema = load_schema()

    valid_record = {
        "evidence_id": "EVD-20260714-ABC123",
        "timestamp": "2026-07-14T10:00:00Z",
        "event_type": "EVIDENCE_SIGNING",
        "provider_id": "ASO-X-PROV-01",
        "payload_hash": "sha256:" + ("a" * 64),
    }

    jsonschema.validate(instance=valid_record, schema=schema)


def test_bare_payload_hash_is_rejected():
    schema = load_schema()

    invalid_record = {
        "evidence_id": "EVD-20260714-ABC123",
        "timestamp": "2026-07-14T10:00:00Z",
        "event_type": "EVIDENCE_SIGNING",
        "provider_id": "ASO-X-PROV-01",
        "payload_hash": "a" * 64,
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_record, schema=schema)


def test_wrong_hash_prefix_is_rejected():
    schema = load_schema()

    invalid_record = {
        "evidence_id": "EVD-20260714-ABC123",
        "timestamp": "2026-07-14T10:00:00Z",
        "event_type": "EVIDENCE_SIGNING",
        "provider_id": "ASO-X-PROV-01",
        "payload_hash": "sha512:" + ("a" * 64),
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_record, schema=schema)
def test_schema_disallows_additional_properties():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    assert schema["additionalProperties"] is False
