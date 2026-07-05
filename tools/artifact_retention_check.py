from __future__ import annotations

import json
import re
import sys
from pathlib import PurePosixPath
from typing import Any

SCHEMA_PREFIX = "aso-x.artifact_retention."
UTC_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")

VALID_RETENTION_CLASSES = {
    "baseline",
    "audit",
    "release",
    "security",
    "durability",
}

VALID_RETENTION_MODES = {
    "retain",
    "archive",
}

VALID_REVIEW_CYCLES = {
    "quarterly",
    "semiannual",
    "annual",
}

VALID_CATEGORIES = {
    "release-evidence",
    "supply-chain",
    "sbom",
    "provenance",
    "policy",
    "test",
    "documentation",
}

VALID_REVIEW_STATUS = {
    "current",
    "scheduled",
}

REQUIRED_TOP_LEVEL_KEYS = [
    "schema_version",
    "retention_policy_id",
    "generated_at_utc",
    "source_repository",
    "branch",
    "commit",
    "retention_class",
    "default_retention",
    "artifacts",
    "review",
    "release_evidence_bundle_path",
    "supply_chain_integrity_path",
    "sbom_path",
    "provenance_attestation_path",
    "network_free_validation",
    "mutable_external_sources_allowed",
    "policy_audit_passed",
    "validation_evidence",
]

REQUIRED_ARTIFACT_KEYS = [
    "name",
    "path",
    "category",
    "retention_years",
    "immutable",
    "required_for_audit",
    "required_for_release",
    "notes",
]

REQUIRED_REVIEW_KEYS = [
    "owner",
    "last_reviewed_at_utc",
    "next_review_due_utc",
    "review_status",
]

REQUIRED_VALIDATION_EVIDENCE_KEYS = [
    "validator_command",
    "test_command",
    "validator_exit_code",
    "test_exit_code",
]


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_safe_repo_relative_path(value: Any) -> bool:
    if not _is_non_empty_string(value):
        return False
    if "\\" in value:
        return False
    if re.match(r"^[A-Za-z]:/", value):
        return False
    if value.startswith("/"):
        return False

    path = PurePosixPath(value)
    parts = path.parts
    if not parts:
        return False
    if any(part in ("", ".", "..") for part in parts):
        return False
    return True


def _validate_default_retention(default_retention: Any, errors: list[str]) -> None:
    if not isinstance(default_retention, dict):
        errors.append("default_retention must be an object")
        return

    for key in ["mode", "minimum_years", "immutable", "review_cycle"]:
        if key not in default_retention:
            errors.append(f"default_retention missing key: {key}")

    mode = default_retention.get("mode")
    if mode not in VALID_RETENTION_MODES:
        errors.append(
            "default_retention.mode must be one of: "
            + ", ".join(sorted(VALID_RETENTION_MODES))
        )

    minimum_years = default_retention.get("minimum_years")
    if not isinstance(minimum_years, int) or minimum_years < 1:
        errors.append("default_retention.minimum_years must be an integer >= 1")

    if default_retention.get("immutable") is not True:
        errors.append("default_retention.immutable must be true")

    review_cycle = default_retention.get("review_cycle")
    if review_cycle not in VALID_REVIEW_CYCLES:
        errors.append(
            "default_retention.review_cycle must be one of: "
            + ", ".join(sorted(VALID_REVIEW_CYCLES))
        )


def _validate_artifacts(artifacts: Any, errors: list[str]) -> None:
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("artifacts must be a non-empty list")
        return

    for index, artifact in enumerate(artifacts):
        prefix = f"artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{prefix} must be an object")
            continue

        for key in REQUIRED_ARTIFACT_KEYS:
            if key not in artifact:
                errors.append(f"{prefix} missing key: {key}")

        if not _is_non_empty_string(artifact.get("name")):
            errors.append(f"{prefix}.name must be a non-empty string")

        if not _is_safe_repo_relative_path(artifact.get("path")):
            errors.append(f"{prefix}.path must be a safe repository-relative path")

        if artifact.get("category") not in VALID_CATEGORIES:
            errors.append(
                f"{prefix}.category must be one of: "
                + ", ".join(sorted(VALID_CATEGORIES))
            )

        retention_years = artifact.get("retention_years")
        if not isinstance(retention_years, int) or retention_years < 1:
            errors.append(f"{prefix}.retention_years must be an integer >= 1")

        if artifact.get("immutable") is not True:
            errors.append(f"{prefix}.immutable must be true")

        if not isinstance(artifact.get("required_for_audit"), bool):
            errors.append(f"{prefix}.required_for_audit must be boolean")

        if not isinstance(artifact.get("required_for_release"), bool):
            errors.append(f"{prefix}.required_for_release must be boolean")

        if not _is_non_empty_string(artifact.get("notes")):
            errors.append(f"{prefix}.notes must be a non-empty string")


def _validate_review(review: Any, errors: list[str]) -> None:
    if not isinstance(review, dict):
        errors.append("review must be an object")
        return

    for key in REQUIRED_REVIEW_KEYS:
        if key not in review:
            errors.append(f"review missing key: {key}")

    if not _is_non_empty_string(review.get("owner")):
        errors.append("review.owner must be a non-empty string")

    last_reviewed = review.get("last_reviewed_at_utc")
    next_due = review.get("next_review_due_utc")

    if not isinstance(last_reviewed, str) or not UTC_Z_RE.fullmatch(last_reviewed):
        errors.append("review.last_reviewed_at_utc must be an ISO-8601 UTC timestamp ending with Z")

    if not isinstance(next_due, str) or not UTC_Z_RE.fullmatch(next_due):
        errors.append("review.next_review_due_utc must be an ISO-8601 UTC timestamp ending with Z")

    if (
        isinstance(last_reviewed, str)
        and isinstance(next_due, str)
        and UTC_Z_RE.fullmatch(last_reviewed)
        and UTC_Z_RE.fullmatch(next_due)
        and next_due < last_reviewed
    ):
        errors.append("review.next_review_due_utc must be >= review.last_reviewed_at_utc")

    if review.get("review_status") not in VALID_REVIEW_STATUS:
        errors.append(
            "review.review_status must be one of: "
            + ", ".join(sorted(VALID_REVIEW_STATUS))
        )


def _validate_validation_evidence(validation_evidence: Any, errors: list[str]) -> None:
    if not isinstance(validation_evidence, dict):
        errors.append("validation_evidence must be an object")
        return

    for key in REQUIRED_VALIDATION_EVIDENCE_KEYS:
        if key not in validation_evidence:
            errors.append(f"validation_evidence missing key: {key}")

    if not _is_non_empty_string(validation_evidence.get("validator_command")):
        errors.append("validation_evidence.validator_command must be a non-empty string")

    if not _is_non_empty_string(validation_evidence.get("test_command")):
        errors.append("validation_evidence.test_command must be a non-empty string")

    if validation_evidence.get("validator_exit_code") != 0:
        errors.append("validation_evidence.validator_exit_code must equal 0")

    if validation_evidence.get("test_exit_code") != 0:
        errors.append("validation_evidence.test_exit_code must equal 0")


def validate_artifact(artifact: Any) -> list[str]:
    errors: list[str] = []

    if not isinstance(artifact, dict):
        return ["artifact must be a JSON object"]

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in artifact:
            errors.append(f"missing required key: {key}")

    schema_version = artifact.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version.startswith(SCHEMA_PREFIX):
        errors.append(f"schema_version must start with {SCHEMA_PREFIX}")

    if not _is_non_empty_string(artifact.get("retention_policy_id")):
        errors.append("retention_policy_id must be a non-empty string")

    generated_at = artifact.get("generated_at_utc")
    if not isinstance(generated_at, str) or not UTC_Z_RE.fullmatch(generated_at):
        errors.append("generated_at_utc must be an ISO-8601 UTC timestamp ending with Z")

    if not _is_non_empty_string(artifact.get("source_repository")):
        errors.append("source_repository must be a non-empty string")

    if not _is_non_empty_string(artifact.get("branch")):
        errors.append("branch must be a non-empty string")

    commit = artifact.get("commit")
    if not isinstance(commit, str) or not SHA1_RE.fullmatch(commit):
        errors.append("commit must be a lowercase 40-character hex SHA-1")

    retention_class = artifact.get("retention_class")
    if retention_class not in VALID_RETENTION_CLASSES:
        errors.append(
            "retention_class must be one of: "
            + ", ".join(sorted(VALID_RETENTION_CLASSES))
        )

    _validate_default_retention(artifact.get("default_retention"), errors)
    _validate_artifacts(artifact.get("artifacts"), errors)
    _validate_review(artifact.get("review"), errors)

    for path_key in [
        "release_evidence_bundle_path",
        "supply_chain_integrity_path",
        "sbom_path",
        "provenance_attestation_path",
    ]:
        if not _is_safe_repo_relative_path(artifact.get(path_key)):
            errors.append(f"{path_key} must be a safe repository-relative path")

    if artifact.get("network_free_validation") is not True:
        errors.append("network_free_validation must be true")

    if artifact.get("mutable_external_sources_allowed") is not False:
        errors.append("mutable_external_sources_allowed must be false")

    if artifact.get("policy_audit_passed") is not True:
        errors.append("policy_audit_passed must be true")

    _validate_validation_evidence(artifact.get("validation_evidence"), errors)

    return errors


def main() -> int:
    artifact_path = "docs/security/audit/sample-artifact-retention.json"
    with open(artifact_path, "r", encoding="utf-8") as fh:
        artifact = json.load(fh)

    errors = validate_artifact(artifact)
    result = {
        "artifact": artifact_path,
        "errors": errors,
        "ok": not errors,
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())