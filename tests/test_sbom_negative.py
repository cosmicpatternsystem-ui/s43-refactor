from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from tools.sbom_check import DEFAULT_ARTIFACT, validate_sbom_artifact


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = REPO_ROOT / DEFAULT_ARTIFACT


def load_sample() -> dict[str, Any]:
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def assert_invalid(data: dict[str, Any], expected_fragment: str) -> None:
    errors = validate_sbom_artifact(data)
    assert errors
    assert any(expected_fragment in error for error in errors), errors


def test_missing_required_key_fails() -> None:
    data = load_sample()
    del data["commit"]

    assert_invalid(data, "missing required key: commit")


def test_invalid_schema_prefix_fails() -> None:
    data = load_sample()
    data["schema_version"] = "wrong.sbom.v1"

    assert_invalid(data, "schema_version must start with")


def test_invalid_commit_fails() -> None:
    data = load_sample()
    data["commit"] = "ABC123"

    assert_invalid(data, "commit must be a lowercase 40-character SHA-1")


def test_invalid_timestamp_fails() -> None:
    data = load_sample()
    data["generated_at_utc"] = "2026-07-05 06:05:00"

    assert_invalid(data, "generated_at_utc must use")


def test_invalid_format_fails() -> None:
    data = load_sample()
    data["format"] = "freeform"

    assert_invalid(data, "format must be one of")


def test_empty_components_fails() -> None:
    data = load_sample()
    data["components"] = []

    assert_invalid(data, "components must be a non-empty list")


def test_component_missing_version_and_status_fails() -> None:
    data = load_sample()
    data["components"] = [
        {
            "name": "component-without-version",
            "type": "library",
        }
    ]

    assert_invalid(data, "must include either version or version_status")


def test_component_invalid_type_fails() -> None:
    data = load_sample()
    data["components"][0]["type"] = "unknown"

    assert_invalid(data, "type must be one of")


def test_component_absolute_path_fails() -> None:
    data = load_sample()
    data["components"][0]["path"] = "/tmp/file"

    assert_invalid(data, "path must be a safe repository-relative path")


def test_component_windows_absolute_path_fails() -> None:
    data = load_sample()
    data["components"][0]["path"] = "C:/tmp/file"

    assert_invalid(data, "path must be a safe repository-relative path")


def test_component_parent_path_fails() -> None:
    data = load_sample()
    data["components"][0]["path"] = "../outside"

    assert_invalid(data, "path must be a safe repository-relative path")


def test_supply_chain_integrity_parent_path_fails() -> None:
    data = load_sample()
    data["supply_chain_integrity_path"] = "../outside.json"

    assert_invalid(data, "supply_chain_integrity_path must be")


def test_release_evidence_absolute_path_fails() -> None:
    data = load_sample()
    data["release_evidence_bundle_path"] = "/tmp/release.json"

    assert_invalid(data, "release_evidence_bundle_path must be")


def test_network_free_validation_false_fails() -> None:
    data = load_sample()
    data["network_free_validation"] = False

    assert_invalid(data, "network_free_validation must be true")


def test_mutable_external_sources_allowed_true_fails() -> None:
    data = load_sample()
    data["mutable_external_sources_allowed"] = True

    assert_invalid(data, "mutable_external_sources_allowed must be false")


def test_policy_audit_passed_false_fails() -> None:
    data = load_sample()
    data["policy_audit_passed"] = False

    assert_invalid(data, "policy_audit_passed must be true")


def test_validation_evidence_missing_key_fails() -> None:
    data = load_sample()
    del data["validation_evidence"]["test_command"]

    assert_invalid(data, "validation_evidence missing required key: test_command")


def test_validator_exit_code_nonzero_fails() -> None:
    data = load_sample()
    data["validation_evidence"]["validator_exit_code"] = 1

    assert_invalid(data, "validation_evidence.validator_exit_code must be 0")


def test_test_exit_code_nonzero_fails() -> None:
    data = load_sample()
    data["validation_evidence"]["test_exit_code"] = 1

    assert_invalid(data, "validation_evidence.test_exit_code must be 0")


def test_artifact_must_be_object() -> None:
    errors = validate_sbom_artifact(["not", "an", "object"])

    assert errors == ["artifact must be a JSON object"]


def test_mutation_does_not_modify_original_sample() -> None:
    data = load_sample()
    original = copy.deepcopy(data)

    mutated = copy.deepcopy(data)
    mutated["components"][0]["path"] = "../bad"

    assert validate_sbom_artifact(mutated)
    assert data == original