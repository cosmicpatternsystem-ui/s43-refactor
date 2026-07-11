from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write_json_no_bom(path: Path, payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def _run_validate(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "asoctl.py",
            "evidence",
            "validate",
            "--path",
            str(path),
        ],
        capture_output=True,
        text=True,
    )


def test_p33_validator_cli_reject_incomplete(tmp_path: Path) -> None:
    bad_record = tmp_path / "bad.json"
    bad_payload = {
        "schema_version": "1.0.0",
        "evidence_id": "evidence-test-incomplete",
        "producer": "tester",
        "subject": "ASO-X",
        "retention": "50y"
    }
    _write_json_no_bom(bad_record, bad_payload)

    result = _run_validate(bad_record)

    assert result.returncode == 1, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["decision"] == "fail"
    assert payload["schema"] == "aso.evidence.validate.v1"
    assert payload["evidence_path"].endswith("bad.json")
    assert isinstance(payload.get("errors"), list)
    assert payload["errors"], payload
    joined = "\n".join(payload["errors"]).lower()
    assert (
        "required property" in joined
        or "required properties" in joined
        or "missing" in joined
        or "additional properties" in joined
        or "unexpected properties" in joined
    ), payload


def test_p33_validator_cli_pass_valid(tmp_path: Path) -> None:
    good_record = tmp_path / "good.json"
    data = {
        "schema_version": "1.0.0",
        "evidence_id": "evidence-test-valid",
        "retention": "50y",
        "subject": "ASO-X",
        "producer": "tester",
        "decision_id": "DEC-001",
        "decision_category": "governance",
        "source_input_reference": "tests/input.txt",
        "ai_output_reference": "tests/output.txt",
        "governing_policy_refs": ["POL-001"],
        "operator_disposition": "accepted",
        "final_status": "accepted-for-review",
        "owner_role": "engineer",
        "created_at_utc": "2026-07-08T00:00:00Z",
        "secret_handling": {
            "contains_secrets": False,
            "redaction_status": "not-required"
        }
    }
    _write_json_no_bom(good_record, data)

    result = _run_validate(good_record)

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["decision"] == "pass"
    assert payload["schema"] == "aso.evidence.validate.v1"
    assert payload["evidence_path"].endswith("good.json")
    assert payload["schema_path"].endswith("repo/schemas/evidence_record.schema.json")