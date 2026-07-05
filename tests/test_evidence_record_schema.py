from __future__ import annotations

import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "evidence-record.schema.json"


def load_schema() -> dict:
with SCHEMA_PATH.open("r", encoding="utf-8") as fh:
return json.load(fh)


def test_evidence_record_schema_is_valid_json_schema() -> None:
schema = load_schema()
jsonschema.Draft202012Validator.check_schema(schema)


def test_minimal_evidence_record_is_valid() -> None:
schema = load_schema()

record = {
"schema_version": "1.0.0",
"evidence_id": "evd_p32_minimal_0001",
"evidence_type": "roadmap_milestone",
"created_at": "2026-07-05T00:00:00Z",
"producer": {
"type": "automation",
"name": "aso-x",
},
"subject": {
"repo": "cosmicpatternsystem-ui/s43-refactor",
"ref": "P3.2",
},
"summary": "Evidence record schema introduced for ASO-X P3.2.",
"integrity": {
"hash_algorithm": "none",
"canonicalization": "none",
},
"retention": {
"class": "permanent",
"minimum_years": 50,
"immutable": True,
"reason": "Governance evidence for the ASO-X durable roadmap.",
},
}

jsonschema.validate(instance=record, schema=schema)


def test_evidence_record_rejects_unknown_top_level_fields() -> None:
schema = load_schema()

record = {
"schema_version": "1.0.0",
"evidence_id": "evd_p32_invalid_0001",
"evidence_type": "roadmap_milestone",
"created_at": "2026-07-05T00:00:00Z",
"producer": {
"type": "automation",
"name": "aso-x",
},
"subject": {
"repo": "cosmicpatternsystem-ui/s43-refactor",
"ref": "P3.2",
},
"summary": "This record must fail because it has an unknown field.",
"integrity": {
"hash_algorithm": "none",
"canonicalization": "none",
},
"retention": {
"class": "permanent",
"minimum_years": 50,
},
"unexpected_field": "must fail",
}

validator = jsonschema.Draft202012Validator(schema)
errors = list(validator.iter_errors(record))

assert errors
assert any("Additional properties are not allowed" in error.message for error in errors)


def test_evidence_record_requires_core_fields() -> None:
schema = load_schema()

record = {
"schema_version": "1.0.0",
"evidence_id": "evd_p32_missing_0001",
}

validator = jsonschema.Draft202012Validator(schema)
errors = list(validator.iter_errors(record))
missing_messages = "\n".join(error.message for error in errors)

assert "'evidence_type' is a required property" in missing_messages
assert "'created_at' is a required property" in missing_messages
assert "'producer' is a required property" in missing_messages
assert "'subject' is a required property" in missing_messages
assert "'summary' is a required property" in missing_messages
assert "'integrity' is a required property" in missing_messages
assert "'retention' is a required property" in missing_messages
