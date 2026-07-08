from __future__ import annotations

from tools.artifact_retention_check import validate_artifact


def _valid_artifact() -> dict:
    return {
        "schema_version": "aso-x.artifact_retention.v1",
        "retention_policy_id": "retention-2026-07-05.1",
        "generated_at_utc": "2026-07-05T06:35:00Z",
        "source_repository": "cosmicpatternsystem-ui/s43-refactor",
        "branch": "main",
        "commit": "1234567890abcdef1234567890abcdef12345678",
        "retention_class": "durability",
        "default_retention": {
            "mode": "retain",
            "minimum_years": 50,
            "immutable": True,
            "review_cycle": "annual"
        },
        "artifacts": [
            {
                "name": "sbom-baseline",
                "path": "docs/security/audit/sample-sbom.json",
                "category": "sbom",
                "retention_years": 50,
                "immutable": True,
                "required_for_audit": True,
                "required_for_release": True,
                "notes": "SBOM retention baseline."
            }
        ],
        "review": {
            "owner": "aso-x-governance",
            "last_reviewed_at_utc": "2026-07-05T06:35:00Z",
            "next_review_due_utc": "2027-07-05T06:35:00Z",
            "review_status": "current"
        },
        "release_evidence_bundle_path": "docs/release/audit/sample-release-evidence-bundle.json",
        "supply_chain_integrity_path": "docs/security/audit/sample-supply-chain-integrity.json",
        "sbom_path": "docs/security/audit/sample-sbom.json",
        "provenance_attestation_path": "docs/security/audit/sample-provenance-attestation.json",
        "network_free_validation": True,
        "mutable_external_sources_allowed": False,
        "policy_audit_passed": True,
        "validation_evidence": {
            "validator_command": "python tools/artifact_retention_check.py",
            "test_command": "python -m pytest tests/test_artifact_retention.py tests/test_artifact_retention_negative.py -q",
            "validator_exit_code": 0,
            "test_exit_code": 0
        }
    }


def test_missing_required_key_fails() -> None:
    artifact = _valid_artifact()
    del artifact["commit"]
    errors = validate_artifact(artifact)
    assert any("missing required key: commit" in error for error in errors)


def test_invalid_schema_prefix_fails() -> None:
    artifact = _valid_artifact()
    artifact["schema_version"] = "aso-x.invalid.v1"
    errors = validate_artifact(artifact)
    assert any("schema_version must start with aso-x.artifact_retention." in error for error in errors)


def test_invalid_commit_fails() -> None:
    artifact = _valid_artifact()
    artifact["commit"] = "BAD"
    errors = validate_artifact(artifact)
    assert any("commit must be a lowercase 40-character hex SHA-1" in error for error in errors)


def test_invalid_timestamp_fails() -> None:
    artifact = _valid_artifact()
    artifact["generated_at_utc"] = "2026-07-05 06:35:00"
    errors = validate_artifact(artifact)
    assert any("generated_at_utc must be an ISO-8601 UTC timestamp ending with Z" in error for error in errors)


def test_invalid_retention_class_fails() -> None:
    artifact = _valid_artifact()
    artifact["retention_class"] = "temporary"
    errors = validate_artifact(artifact)
    assert any("retention_class must be one of:" in error for error in errors)


def test_invalid_default_retention_mode_fails() -> None:
    artifact = _valid_artifact()
    artifact["default_retention"]["mode"] = "delete"
    errors = validate_artifact(artifact)
    assert any("default_retention.mode must be one of:" in error for error in errors)


def test_invalid_default_retention_years_fails() -> None:
    artifact = _valid_artifact()
    artifact["default_retention"]["minimum_years"] = 0
    errors = validate_artifact(artifact)
    assert any("default_retention.minimum_years must be an integer >= 1" in error for error in errors)


def test_artifacts_empty_fails() -> None:
    artifact = _valid_artifact()
    artifact["artifacts"] = []
    errors = validate_artifact(artifact)
    assert any("artifacts must be a non-empty list" in error for error in errors)


def test_invalid_artifact_category_fails() -> None:
    artifact = _valid_artifact()
    artifact["artifacts"][0]["category"] = "unknown"
    errors = validate_artifact(artifact)
    assert any("artifacts[0].category must be one of:" in error for error in errors)


def test_invalid_artifact_path_fails() -> None:
    artifact = _valid_artifact()
    artifact["artifacts"][0]["path"] = "../outside.json"
    errors = validate_artifact(artifact)
    assert any("artifacts[0].path must be a safe repository-relative path" in error for error in errors)


def test_invalid_review_order_fails() -> None:
    artifact = _valid_artifact()
    artifact["review"]["last_reviewed_at_utc"] = "2027-07-05T06:35:00Z"
    artifact["review"]["next_review_due_utc"] = "2026-07-05T06:35:00Z"
    errors = validate_artifact(artifact)
    assert any("review.next_review_due_utc must be >= review.last_reviewed_at_utc" in error for error in errors)


def test_absolute_release_evidence_path_fails() -> None:
    artifact = _valid_artifact()
    artifact["release_evidence_bundle_path"] = "/tmp/file.json"
    errors = validate_artifact(artifact)
    assert any("release_evidence_bundle_path must be a safe repository-relative path" in error for error in errors)


def test_windows_absolute_sbom_path_fails() -> None:
    artifact = _valid_artifact()
    artifact["sbom_path"] = "C:/tmp/file.json"
    errors = validate_artifact(artifact)
    assert any("sbom_path must be a safe repository-relative path" in error for error in errors)


def test_parent_provenance_path_fails() -> None:
    artifact = _valid_artifact()
    artifact["provenance_attestation_path"] = "../outside.json"
    errors = validate_artifact(artifact)
    assert any("provenance_attestation_path must be a safe repository-relative path" in error for error in errors)


def test_network_free_validation_false_fails() -> None:
    artifact = _valid_artifact()
    artifact["network_free_validation"] = False
    errors = validate_artifact(artifact)
    assert any("network_free_validation must be true" in error for error in errors)


def test_mutable_external_sources_allowed_true_fails() -> None:
    artifact = _valid_artifact()
    artifact["mutable_external_sources_allowed"] = True
    errors = validate_artifact(artifact)
    assert any("mutable_external_sources_allowed must be false" in error for error in errors)


def test_policy_audit_passed_false_fails() -> None:
    artifact = _valid_artifact()
    artifact["policy_audit_passed"] = False
    errors = validate_artifact(artifact)
    assert any("policy_audit_passed must be true" in error for error in errors)


def test_missing_validation_evidence_key_fails() -> None:
    artifact = _valid_artifact()
    del artifact["validation_evidence"]["validator_exit_code"]
    errors = validate_artifact(artifact)
    assert any("validation_evidence missing key: validator_exit_code" in error for error in errors)


def test_nonzero_validator_exit_code_fails() -> None:
    artifact = _valid_artifact()
    artifact["validation_evidence"]["validator_exit_code"] = 1
    errors = validate_artifact(artifact)
    assert any("validation_evidence.validator_exit_code must equal 0" in error for error in errors)


def test_nonzero_test_exit_code_fails() -> None:
    artifact = _valid_artifact()
    artifact["validation_evidence"]["test_exit_code"] = 2
    errors = validate_artifact(artifact)
    assert any("validation_evidence.test_exit_code must equal 0" in error for error in errors)


def test_artifact_must_be_object() -> None:
    errors = validate_artifact(["not", "an", "object"])
    assert errors == ["artifact must be a JSON object"]