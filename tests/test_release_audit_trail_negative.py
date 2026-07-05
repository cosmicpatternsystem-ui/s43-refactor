import json

from tools.release_audit_trail_check import validate_audit_artifact


def test_validator_rejects_missing_required_keys(tmp_path):
    path = tmp_path / "bad-audit.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "aso-x.release_audit_trail.v1",
                "release_id": "r1",
            },
            indent=2,
        ),
        encoding="utf-8",
        newline="\n",
    )

    errors = validate_audit_artifact(path)

    assert "missing key: generated_at_utc" in errors
    assert "missing key: branch" in errors
    assert "missing key: commit" in errors
    assert "missing key: policy_audit_passed" in errors
    assert "missing key: checks" in errors
    assert "missing key: approvers" in errors


def test_validator_rejects_invalid_types(tmp_path):
    path = tmp_path / "bad-types.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "aso-x.release_audit_trail.v1",
                "release_id": "r2",
                "generated_at_utc": "2026-07-05T05:15:00Z",
                "branch": "",
                "commit": "",
                "policy_audit_passed": "yes",
                "checks": [],
                "approvers": {},
            },
            indent=2,
        ),
        encoding="utf-8",
        newline="\n",
    )

    errors = validate_audit_artifact(path)

    assert "branch must be a non-empty string" in errors
    assert "commit must be a non-empty string" in errors
    assert "policy_audit_passed must be boolean" in errors
    assert "checks must be a non-empty array" in errors
    assert "approvers must be an array" in errors
