import pytest
import json
import subprocess
import sys
from pathlib import Path

def test_p33_validator_cli_reject_incomplete(tmp_path):
    bad_record = tmp_path / "bad_evidence.json"
    bad_record.write_text(json.dumps({"schema_version": "1.0", "summary": "incomplete"}), encoding='utf-8')
    
    result = subprocess.run(
        [sys.executable, "asoctl.py", "evidence", "validate", "--path", str(bad_record)],
        capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "missing_fields" in result.stdout

def test_p33_validator_cli_pass_valid(tmp_path):
    good_record = tmp_path / "good_evidence.json"
    data = {
        "schema_version": "1.0", "evidence_id": "EV-TEST", "evidence_type": "test",
        "created_at": "2026-07-08T00:00:00Z", "producer": "tester", "subject": "ASO-X",
        "summary": "Valid record", "integrity": "sha256:12345", "retention": "50y"
    }
    good_record.write_text(json.dumps(data), encoding='utf-8')
    
    result = subprocess.run(
        [sys.executable, "asoctl.py", "evidence", "validate", "--path", str(good_record)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert '"status": "pass"' in result.stdout
