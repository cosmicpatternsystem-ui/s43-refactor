from __future__ import annotations

import json
from pathlib import Path

from tools.supply_chain_integrity_check import validate_supply_chain_integrity


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def valid_payload() -> dict:
    return {
        "schema_version": "aso-x.supply_chain_integrity.v1",
        "artifact_id": "sci-2026-07-05.1",
        "generated_at_utc": "2026-07-05T05:45:00Z",
        "source_repository": "cosmicpatternsystem-ui/s43-refactor",
        "branch": "main",
        "commit": "8305dd6fcaa7737f623c25010532d64816993df7",
        "policy_document_path": "docs/security/supply-chain-integrity-policy.md",
        "release_evidence_bundle_path": "docs/release/audit/sample-release-evidence-bundle.json",
        "tracked_dependency_files": [
            "dashboard/package-lock.json",
            "dashboard/package.json",
            "requirements-dev.txt",
            "requirements.txt"
        ],
        "dependency_lockfiles_present": True,
        "network_free_validation": True,
        "mutable_external_sources_allowed": False,
        "validation_evidence": {
            "validator_command": "python tools/supply_chain_integrity_check.py",
            "test_command": "python -m pytest tests/test_supply_chain_integrity.py tests/test_supply_chain_integrity_negative.py -q",
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

    errors = validate_supply_chain_integrity(path)
    assert any("missing required keys" in error for error in errors)


def test_invalid_commit_fails(tmp_path: Path) -> None:
    payload = valid_payload()
    payload["commit"] = "INVALID"
    path = tmp_path / "invalid-commit.json"
    write_json(path, payload)

    errors = validate_supply_chain_integrity(path)
    assert "commit must be a 40-character lowercase hexadecimal string" in errors


def test_empty_tracked_dependency_files_fails(tmp_path: Path) -> None:
    payload = valid_payload()
    payload["tracked_dependency_files"] = []
    path = tmp_path / "empty-dependencies.json"
    write_json(path, payload)

    errors = validate_supply_chain_integrity(path)
    assert "tracked_dependency_files must be a non-empty list" in errors


def test_absolute_dependency_path_fails(tmp_path: Path) -> None:
    payload = valid_payload()
    payload["tracked_dependency_files"] = ["/tmp/requirements.txt"]
    path = tmp_path / "absolute-path.json"
    write_json(path, payload)

    errors = validate_supply_chain_integrity(path)
    assert "tracked_dependency_files[0] must be a repository-relative path string" in errors


def test_parent_dependency_path_fails(tmp_path: Path) -> None:
    payload = valid_payload()
    payload["tracked_dependency_files"] = ["../requirements.txt"]
    path = tmp_path / "parent-path.json"
    write_json(path, payload)

    errors = validate_supply_chain_integrity(path)
    assert "tracked_dependency_files[0] must be a repository-relative path string" in errors


def test_network_free_validation_false_fails(tmp_path: Path) -> None:
    payload = valid_payload()
    payload["network_free_validation"] = False
    path = tmp_path / "network-validation.json"
    write_json(path, payload)

    errors = validate_supply_chain_integrity(path)
    assert "network_free_validation must be true" in errors


def test_mutable_external_sources_allowed_true_fails(tmp_path: Path) -> None:
    payload = valid_payload()
    payload["mutable_external_sources_allowed"] = True
    path = tmp_path / "mutable-sources.json"
    write_json(path, payload)

    errors = validate_supply_chain_integrity(path)
    assert "mutable_external_sources_allowed must be false" in errors


def test_nonzero_validator_exit_code_fails(tmp_path: Path) -> None:
    payload = valid_payload()
    payload["validation_evidence"]["validator_exit_code"] = 1
    path = tmp_path / "validator-exit-code.json"
    write_json(path, payload)

    errors = validate_supply_chain_integrity(path)
    assert "validation_evidence.validator_exit_code must equal 0" in errors


def test_policy_audit_passed_false_fails(tmp_path: Path) -> None:
    payload = valid_payload()
    payload["policy_audit_passed"] = False
    path = tmp_path / "policy-audit-false.json"
    write_json(path, payload)

    errors = validate_supply_chain_integrity(path)
    assert "policy_audit_passed must be true" in errors