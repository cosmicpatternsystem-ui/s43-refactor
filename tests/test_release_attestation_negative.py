from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.release_attestation_check import validate_attestation_artifact


def _valid_artifact() -> dict[str, Any]:
    return {
        "schema_version": "aso-x.release_attestation.v1",
        "release_id": "sample-2026-07-05.1",
        "attested_at_utc": "2026-07-05T05:30:00Z",
        "branch": "main",
        "commit": "5382ed1000000000000000000000000000000000",
        "artifact_path": "docs/release/audit/sample-release-audit.json",
        "artifact_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
        "policy_audit_passed": True,
        "attestors": [
            "release-manager",
            "compliance-reviewer",
        ],
    }


def _write_artifact(tmp_path: Path, data: dict[str, Any]) -> Path:
    path = tmp_path / "attestation.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_missing_required_key_is_rejected(tmp_path: Path) -> None:
    data = _valid_artifact()
    del data["commit"]

    errors = validate_attestation_artifact(_write_artifact(tmp_path, data))

    assert "missing required key: commit" in errors


def test_invalid_commit_is_rejected(tmp_path: Path) -> None:
    data = _valid_artifact()
    data["commit"] = "not-a-sha"

    errors = validate_attestation_artifact(_write_artifact(tmp_path, data))

    assert "commit must be a 40-character hexadecimal SHA-1 value" in errors


def test_invalid_artifact_sha256_is_rejected(tmp_path: Path) -> None:
    data = _valid_artifact()
    data["artifact_sha256"] = "bad"

    errors = validate_attestation_artifact(_write_artifact(tmp_path, data))

    assert "artifact_sha256 must be a 64-character hexadecimal SHA-256 value" in errors


def test_empty_attestors_is_rejected(tmp_path: Path) -> None:
    data = _valid_artifact()
    data["attestors"] = []

    errors = validate_attestation_artifact(_write_artifact(tmp_path, data))

    assert "attestors must be a non-empty array" in errors


def test_policy_audit_passed_must_be_boolean(tmp_path: Path) -> None:
    data = _valid_artifact()
    data["policy_audit_passed"] = "true"

    errors = validate_attestation_artifact(_write_artifact(tmp_path, data))

    assert "policy_audit_passed must be a boolean" in errors
