from __future__ import annotations

import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "src" / "schemas" / "evidence-record.schema.json"


def load_schema() -> dict:
    with SCHEMA_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def make_valid_record() -> dict:
    return {
        "version": "1.0.0",
        "uuid": "123e4567-e89b-12d3-a456-426614174000",
        "timestamp": "2026-07-05T00:00:00Z",
        "producer": "aso-x",
        "event_type": "pipeline_gate_pass",
        "payload_hash": "sha256:" + ("a" * 64),
        "signatures": [
            {
                "key_id": "test-key-1",
                "signature": "deadbeefcafebabe",
            }
        ],
    }


def test_evidence_record_schema_is_valid_json_schema() -> None:
    schema = load_schema()
    jsonschema.Draft202012Validator.check_schema(schema)


def test_minimal_evidence_record_is_valid() -> None:
    schema = load_schema()
    record = make_valid_record()
    jsonschema.validate(instance=record, schema=schema)


def test_evidence_record_rejects_unknown_top_level_fields() -> None:
    schema = load_schema()
    record = make_valid_record()
    record["unexpected_field"] = "must fail"

    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(record))

    assert errors
    assert any(
        "Additional properties are not allowed" in error.message
        for error in errors
    )


def test_evidence_record_requires_core_fields() -> None:
    schema = load_schema()
    record = {
        "version": "1.0.0",
        "uuid": "123e4567-e89b-12d3-a456-426614174000",
    }

    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(record))
    missing_messages = "\n".join(error.message for error in errors)

    assert "'timestamp' is a required property" in missing_messages
    assert "'producer' is a required property" in missing_messages
    assert "'event_type' is a required property" in missing_messages
    assert "'payload_hash' is a required property" in missing_messages
    assert "'signatures' is a required property" in missing_messages
