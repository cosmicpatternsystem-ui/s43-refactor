from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

DEFAULT_ARTIFACT = Path("docs/security/audit/sample-provenance-attestation.json")
SCHEMA_PREFIX = "aso-x.provenance_attestation."
UTC_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _is_safe_repo_relative_path(value: Any) -> bool:
    if not _is_non_empty_string(value):
        return False
    path = str(value).replace("\\", "/")
    if path.startswith("/"):
        return False
    if re.match(r"^[A-Za-z]:/", path):
        return False
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return False
    return True


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8", newline=None) as handle:
        return json.load(handle)


def _validate_subject(subject: Any, errors: list[str]) -> None:
    if not isinstance(subject, dict):
        errors.append("subject must be an object")
        return

    if not _is_non_empty_string(subject.get("name")):
        errors.append("subject.name must be a non-empty string")

    if not _is_non_empty_string(subject.get("type")):
        errors.append("subject.type must be a non-empty string")

    if not _is_safe_repo_relative_path(subject.get("path")):
        errors.append("subject.path must be a safe repository-relative path")

    digest = subject.get("digest_sha256")
    if not (_is_non_empty_string(digest) and SHA256_RE.fullmatch(str(digest))):
        errors.append("subject.digest_sha256 must be a lowercase 64-character hex SHA-256")


def _validate_build_definition(build_definition: Any, errors: list[str]) -> None:
    if not isinstance(build_definition, dict):
        errors.append("build_definition must be an object")
        return

    if not _is_non_empty_string(build_definition.get("build_type")):
        errors.append("build_definition.build_type must be a non-empty string")

    builder = build_definition.get("builder")
    if not isinstance(builder, dict):
        errors.append("build_definition.builder must be an object")
    else:
        if not _is_non_empty_string(builder.get("id")):
            errors.append("build_definition.builder.id must be a non-empty string")
        if not _is_non_empty_string(builder.get("version")):
            errors.append("build_definition.builder.version must be a non-empty string")

    invocation = build_definition.get("invocation")
    if not isinstance(invocation, dict):
        errors.append("build_definition.invocation must be an object")
    else:
        if not _is_non_empty_string(invocation.get("config_source")):
            errors.append("build_definition.invocation.config_source must be a non-empty string")
        if not isinstance(invocation.get("parameters"), dict):
            errors.append("build_definition.invocation.parameters must be an object")
        if not isinstance(invocation.get("environment"), dict):
            errors.append("build_definition.invocation.environment must be an object")


def _validate_predicate(predicate: Any, errors: list[str]) -> None:
    if not isinstance(predicate, dict):
        errors.append("predicate must be an object")
        return

    materials = predicate.get("materials")
    if not isinstance(materials, list) or len(materials) == 0:
        errors.append("predicate.materials must be a non-empty list")
    else:
        for index, material in enumerate(materials):
            if not isinstance(material, dict):
                errors.append(f"predicate.materials[{index}] must be an object")
                continue
            if not _is_non_empty_string(material.get("name")):
                errors.append(f"predicate.materials[{index}].name must be a non-empty string")
            if not _is_non_empty_string(material.get("uri")):
                errors.append(f"predicate.materials[{index}].uri must be a non-empty string")
            digest = material.get("digest")
            if not isinstance(digest, dict) or len(digest) == 0:
                errors.append(f"predicate.materials[{index}].digest must be a non-empty object")
            else:
                for digest_name, digest_value in digest.items():
                    if not _is_non_empty_string(digest_name):
                        errors.append(f"predicate.materials[{index}].digest keys must be non-empty strings")
                    if not _is_non_empty_string(digest_value):
                        errors.append(f"predicate.materials[{index}].digest values must be non-empty strings")

    metadata = predicate.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("predicate.metadata must be an object")
        return

    completeness = metadata.get("completeness")
    if not isinstance(completeness, dict):
        errors.append("predicate.metadata.completeness must be an object")

    if not isinstance(metadata.get("reproducible"), bool):
        errors.append("predicate.metadata.reproducible must be a boolean")

    finished = metadata.get("build_finished_on_utc")
    if not (_is_non_empty_string(finished) and UTC_Z_RE.fullmatch(str(finished))):
        errors.append("predicate.metadata.build_finished_on_utc must be an ISO-8601 UTC timestamp ending with Z")


def validate_artifact(data: Any) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["artifact must be a JSON object"]

    required_keys = [
        "schema_version",
        "attestation_id",
        "generated_at_utc",
        "source_repository",
        "branch",
        "commit",
        "subject",
        "build_definition",
        "predicate",
        "release_evidence_bundle_path",
        "supply_chain_integrity_path",
        "sbom_path",
        "network_free_validation",
        "mutable_external_sources_allowed",
        "policy_audit_passed",
        "validation_evidence",
    ]

    for key in required_keys:
        if key not in data:
            errors.append(f"missing required key: {key}")

    schema_version = data.get("schema_version")
    if not (_is_non_empty_string(schema_version) and str(schema_version).startswith(SCHEMA_PREFIX)):
        errors.append(f"schema_version must start with {SCHEMA_PREFIX}")

    attestation_id = data.get("attestation_id")
    if not _is_non_empty_string(attestation_id):
        errors.append("attestation_id must be a non-empty string")

    generated_at_utc = data.get("generated_at_utc")
    if not (_is_non_empty_string(generated_at_utc) and UTC_Z_RE.fullmatch(str(generated_at_utc))):
        errors.append("generated_at_utc must be an ISO-8601 UTC timestamp ending with Z")

    source_repository = data.get("source_repository")
    if not _is_non_empty_string(source_repository):
        errors.append("source_repository must be a non-empty string")

    branch = data.get("branch")
    if not _is_non_empty_string(branch):
        errors.append("branch must be a non-empty string")

    commit = data.get("commit")
    if not (_is_non_empty_string(commit) and SHA1_RE.fullmatch(str(commit))):
        errors.append("commit must be a lowercase 40-character hex SHA-1")

    _validate_subject(data.get("subject"), errors)
    _validate_build_definition(data.get("build_definition"), errors)
    _validate_predicate(data.get("predicate"), errors)

    for path_key in [
        "release_evidence_bundle_path",
        "supply_chain_integrity_path",
        "sbom_path",
    ]:
        if not _is_safe_repo_relative_path(data.get(path_key)):
            errors.append(f"{path_key} must be a safe repository-relative path")

    if data.get("network_free_validation") is not True:
        errors.append("network_free_validation must be true")

    if data.get("mutable_external_sources_allowed") is not False:
        errors.append("mutable_external_sources_allowed must be false")

    if data.get("policy_audit_passed") is not True:
        errors.append("policy_audit_passed must be true")

    validation_evidence = data.get("validation_evidence")
    if not isinstance(validation_evidence, dict):
        errors.append("validation_evidence must be an object")
    else:
        for key in ["validator_command", "test_command"]:
            if not _is_non_empty_string(validation_evidence.get(key)):
                errors.append(f"validation_evidence.{key} must be a non-empty string")
        for key in ["validator_exit_code", "test_exit_code"]:
            if key not in validation_evidence:
                errors.append(f"validation_evidence missing key: {key}")
            elif validation_evidence.get(key) != 0:
                errors.append(f"validation_evidence.{key} must equal 0")

    return errors


def main(argv: list[str]) -> int:
    artifact = Path(argv[1]) if len(argv) > 1 else DEFAULT_ARTIFACT
    data = _load_json(artifact)
    errors = validate_artifact(data)
    payload = {
        "artifact": str(artifact),
        "errors": errors,
        "ok": len(errors) == 0,
    }
    print(json.dumps(payload, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))