from __future__ import annotations

from tools.provenance_attestation_check import validate_artifact


def _valid_artifact() -> dict:
    return {
        "schema_version": "aso-x.provenance_attestation.v1",
        "attestation_id": "prov-2026-07-05.1",
        "generated_at_utc": "2026-07-05T06:20:00Z",
        "source_repository": "cosmicpatternsystem-ui/s43-refactor",
        "branch": "main",
        "commit": "1234567890abcdef1234567890abcdef12345678",
        "subject": {
            "name": "sample-sbom",
            "type": "audit-artifact",
            "path": "docs/security/audit/sample-sbom.json",
            "digest_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        },
        "build_definition": {
            "build_type": "repository-policy-baseline",
            "builder": {
                "id": "asoctl-policy-pipeline",
                "version": "1"
            },
            "invocation": {
                "config_source": "repo-local",
                "parameters": {
                    "policy": "P2.8"
                },
                "environment": {
                    "runner": "local-or-ci"
                }
            }
        },
        "predicate": {
            "materials": [
                {
                    "name": "sbom-baseline",
                    "uri": "repo:docs/security/audit/sample-sbom.json",
                    "digest": {
                        "gitCommit": "1234567890abcdef1234567890abcdef12345678"
                    }
                }
            ],
            "metadata": {
                "completeness": {
                    "parameters": True,
                    "environment": True,
                    "materials": True
                },
                "reproducible": True,
                "build_finished_on_utc": "2026-07-05T06:20:30Z"
            }
        },
        "release_evidence_bundle_path": "docs/release/audit/sample-release-evidence-bundle.json",
        "supply_chain_integrity_path": "docs/security/audit/sample-supply-chain-integrity.json",
        "sbom_path": "docs/security/audit/sample-sbom.json",
        "network_free_validation": True,
        "mutable_external_sources_allowed": False,
        "policy_audit_passed": True,
        "validation_evidence": {
            "validator_command": "python tools/provenance_attestation_check.py",
            "test_command": "python -m pytest tests/test_provenance_attestation.py tests/test_provenance_attestation_negative.py -q",
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
    assert any("schema_version must start with aso-x.provenance_attestation." in error for error in errors)


def test_invalid_commit_fails() -> None:
    artifact = _valid_artifact()
    artifact["commit"] = "ABC"
    errors = validate_artifact(artifact)
    assert any("commit must be a lowercase 40-character hex SHA-1" in error for error in errors)


def test_invalid_timestamp_fails() -> None:
    artifact = _valid_artifact()
    artifact["generated_at_utc"] = "2026-07-05 06:20:00"
    errors = validate_artifact(artifact)
    assert any("generated_at_utc must be an ISO-8601 UTC timestamp ending with Z" in error for error in errors)


def test_invalid_subject_path_fails() -> None:
    artifact = _valid_artifact()
    artifact["subject"]["path"] = "../outside.json"
    errors = validate_artifact(artifact)
    assert any("subject.path must be a safe repository-relative path" in error for error in errors)


def test_invalid_subject_digest_fails() -> None:
    artifact = _valid_artifact()
    artifact["subject"]["digest_sha256"] = "not-a-sha256"
    errors = validate_artifact(artifact)
    assert any("subject.digest_sha256 must be a lowercase 64-character hex SHA-256" in error for error in errors)


def test_missing_builder_id_fails() -> None:
    artifact = _valid_artifact()
    del artifact["build_definition"]["builder"]["id"]
    errors = validate_artifact(artifact)
    assert any("build_definition.builder.id must be a non-empty string" in error for error in errors)


def test_empty_materials_fails() -> None:
    artifact = _valid_artifact()
    artifact["predicate"]["materials"] = []
    errors = validate_artifact(artifact)
    assert any("predicate.materials must be a non-empty list" in error for error in errors)


def test_empty_material_digest_fails() -> None:
    artifact = _valid_artifact()
    artifact["predicate"]["materials"][0]["digest"] = {}
    errors = validate_artifact(artifact)
    assert any("predicate.materials[0].digest must be a non-empty object" in error for error in errors)


def test_invalid_build_finished_timestamp_fails() -> None:
    artifact = _valid_artifact()
    artifact["predicate"]["metadata"]["build_finished_on_utc"] = "bad"
    errors = validate_artifact(artifact)
    assert any("predicate.metadata.build_finished_on_utc must be an ISO-8601 UTC timestamp ending with Z" in error for error in errors)


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


def test_parent_supply_chain_path_fails() -> None:
    artifact = _valid_artifact()
    artifact["supply_chain_integrity_path"] = "../outside.json"
    errors = validate_artifact(artifact)
    assert any("supply_chain_integrity_path must be a safe repository-relative path" in error for error in errors)


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