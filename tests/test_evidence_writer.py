import pytest
import json
from pathlib import Path
from src.security.evidence_writer import AtomicEvidenceWriter

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "evidence-record.schema.json"

@pytest.fixture
def writer():
    return AtomicEvidenceWriter(schema_path=SCHEMA_PATH)

@pytest.fixture
def valid_record():
    return {
        "version": "1.0.0",
        "uuid": "a8b9c0d1-e2f3-4a5b-6c7d-8e9f0a1b2c3d",
        "timestamp": "2026-07-14T15:30:00Z",
        "producer": "aso-x-policy-engine",
        "event_type": "ledger_rotation",
        "payload_hash": "sha256:8f434346648f98a25c7e11cf892427ae41e4649b934ca495991b7852b855aaab",
        "signatures": [
            {
                "key_id": "kms-key-02",
                "signature": "8f8e8d8c8b8a"
            }
        ]
    }

def test_atomic_write_success(writer, valid_record, tmp_path):
    target = tmp_path / "evidence_record.json"
    writer.write_atomic(target, valid_record)
    
    assert target.exists()
    
    # Verify content and encoding (No-BOM UTF-8, LF)
    raw_bytes = target.read_bytes()
    assert not raw_bytes.startswith(b'\xef\xbb\xbf'), "BOM detected in file!"
    
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data["uuid"] == valid_record["uuid"]
    assert b"\r\n" not in raw_bytes, "CRLF detected! Expected LF only."

def test_atomic_write_schema_failure(writer, valid_record, tmp_path):
    target = tmp_path / "evidence_record_fail.json"
    invalid_record = valid_record.copy()
    invalid_record["event_type"] = "unsupported_event"
    
    with pytest.raises(Exception):
        writer.write_atomic(target, invalid_record)
        
    assert not target.exists(), "Target file created despite schema validation failure!"