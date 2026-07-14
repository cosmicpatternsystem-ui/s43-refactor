import json
import jsonschema
import pytest
import os

SCHEMA_PATH = "evidence_pack/schemas/evidence-record.schema.json"

def test_evidence_schema_alignment():
    """Verify that schema uses event_type and payload_hash."""
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)
    
    assert "event_type" in schema["required"]
    assert "payload_hash" in schema["required"]
    assert "evidence_type" not in schema["properties"]
    assert "content_hash" not in schema["properties"]

def test_valid_record_against_schema():
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)
    
    valid_record = {
        "evidence_id": "EVD-20260714-ABC123",
        "timestamp": "2026-07-14T10:00:00Z",
        "event_type": "EVIDENCE_SIGNING",
        "provider_id": "ASO-X-PROV-01",
        "payload_hash": "a" * 64
    }
    jsonschema.validate(instance=valid_record, schema=schema)
