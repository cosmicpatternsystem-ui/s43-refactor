import json
from pathlib import Path
import jsonschema
import pytest

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "evidence-record.schema.json"

@pytest.fixture
def schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def valid_record():
    return {
        "version": "1.0.0",
        "uuid": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
        "timestamp": "2026-07-14T12:00:00Z",
        "producer": "aso-x-pipeline-gate",
        "event_type": "pipeline_gate_pass",
        "payload_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "signatures": [
            {
                "key_id": "key-01",
                "signature": "a1b2c3d4e5f6"
            }
        ]
    }

def test_valid_record(schema, valid_record):
    jsonschema.validate(instance=valid_record, schema=schema)

def test_invalid_event_type(schema, valid_record):
    valid_record["event_type"] = "invalid_event"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=valid_record, schema=schema)