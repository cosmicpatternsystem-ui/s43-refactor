from __future__ import annotations

import json
from pathlib import Path

from tools.release_evidence_bundle_check import validate_release_evidence_bundle


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def valid_payload() -> dict:
    return {
        "schema_version": "aso-x.release_evidence_bundle.v1",
        "bundle_id": "bundle-2026-07-05.1",
        "release_id": "sample-2026-07-05.1",
        "branch": "main",
        "commit": "d8f545fffe0d128357b3f138a0b1709d8732ddf2",
        "generated_at_utc": "2026-07-05T05:30:00Z",
        "policy_document_path": "docs/release/release-evidence-bundle-policy.md",
        "attestation_path": "docs/release/audit/sample-release-attestation.json",
        "audit_artifact_path": "docs/release/audit/sample-release-audit.json",
        "test_evidence": {
            "validator_command": "python tools/release_evidence_bundle_check.py",
            "test_command": "python -m pytest tests/test_release_evidence_bundle.py tests/test_release_evidence_bundle_negative.py -q",
            "validator_exit_code": 0,
            "test_exit_code": 0
        },
        "policy_audit_passed": True
    }


def test_missing_required_key_fails(tmp_path: Path) -> None:
    payload = valid_payload()
    del payload["commit"]
    path = tmp_path / "missing-key.json"
    write_json(path, payload)

    errors = validate_release_evidence_bundle(path)
    assert any("missing required keys" in error for error in errors)


def test_invalid_commit_fails(tmp_path: Path) -> None:
    payload = valid_payload()
    payload["commit"] = "INVALID"
    path = tmp_path / "invalid-commit.json"
    write_json(path, payload)

    errors = validate_release_evidence_bundle(path)
    assert "commit must be a 40-character lowercase hexadecimal string" in errors


def test_invalid_test_evidence_exit_code_fails(tmp_path: Path) -> None:
    payload = valid_payload()
    payload["test_evidence"]["test_exit_code"] = 1
    path = tmp_path / "invalid-exit-code.json"
    write_json(path, payload)

    errors = validate_release_evidence_bundle(path)
    assert "test_evidence.test_exit_code must equal 0" in errors


def test_empty_attestation_path_fails(tmp_path: Path) -> None:
    payload = valid_payload()
    payload["attestation_path"] = "   "
    path = tmp_path / "empty-attestation-path.json"
    write_json(path, payload)

    errors = validate_release_evidence_bundle(path)
    assert "attestation_path must be a non-empty string" in errors


def test_non_boolean_policy_audit_passed_fails(tmp_path: Path) -> None:
    payload = valid_payload()
    payload["policy_audit_passed"] = "true"
    path = tmp_path / "non-bool-policy-audit.json"
    write_json(path, payload)

    errors = validate_release_evidence_bundle(path)
    assert "policy_audit_passed must be boolean" in errors