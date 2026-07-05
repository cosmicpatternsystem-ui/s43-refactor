#!/usr/bin/env python3
"""Validate ASO-X SBOM baseline artifacts.

This validator is intentionally deterministic and network-free. It validates
the repository baseline SBOM contract introduced by P2.7.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_ARTIFACT = Path("docs/security/audit/sample-sbom.json")

SCHEMA_PREFIX = "aso-x.sbom."

REQUIRED_KEYS = {
    "schema_version",
    "sbom_id",
    "generated_at_utc",
    "source_repository",
    "branch",
    "commit",
    "format",
    "components",
    "supply_chain_integrity_path",
    "release_evidence_bundle_path",
    "network_free_validation",
    "mutable_external_sources_allowed",
    "policy_audit_passed",
    "validation_evidence",
}

VALID_FORMATS = {
    "aso-x-minimal",
    "cyclonedx-json",
    "spdx-json",
}

VALID_COMPONENT_TYPES = {
    "application",
    "library",
    "runtime",
    "tooling",
    "manifest",
    "lockfile",
    "documentation",
    "policy",
    "test",
}

REQUIRED_VALIDATION_EVIDENCE_KEYS = {
    "validator_command",
    "test_command",
    "validator_exit_code",
    "test_exit_code",
}

SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
UTC_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_safe_relative_path(value: Any) -> bool:
    if not _is_non_empty_string(value):
        return False

    path = value.strip().replace("\\", "/")
    if path == ".":
        return True

    if path.startswith("/"):
        return False

    if re.match(r"^[A-Za-z]:/", path):
        return False

    normalized = posixpath.normpath(path)
    if normalized == ".":
        return True

    if normalized.startswith("../") or normalized == "..":
        return False

    if "/../" in f"/{normalized}/":
        return False

    return True


def validate_sbom_artifact(data: Any) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["artifact must be a JSON object"]

    missing = sorted(REQUIRED_KEYS - set(data))
    for key in missing:
        errors.append(f"missing required key: {key}")

    if missing:
        return errors

    schema_version = data.get("schema_version")
    if not _is_non_empty_string(schema_version):
        errors.append("schema_version must be a non-empty string")
    elif not schema_version.startswith(SCHEMA_PREFIX):
        errors.append(f"schema_version must start with {SCHEMA_PREFIX!r}")

    if not _is_non_empty_string(data.get("sbom_id")):
        errors.append("sbom_id must be a non-empty string")

    generated_at_utc = data.get("generated_at_utc")
    if not _is_non_empty_string(generated_at_utc):
        errors.append("generated_at_utc must be a non-empty string")
    elif not UTC_Z_RE.match(generated_at_utc):
        errors.append("generated_at_utc must use YYYY-MM-DDTHH:MM:SSZ format")

    if not _is_non_empty_string(data.get("source_repository")):
        errors.append("source_repository must be a non-empty string")

    if not _is_non_empty_string(data.get("branch")):
        errors.append("branch must be a non-empty string")

    commit = data.get("commit")
    if not _is_non_empty_string(commit):
        errors.append("commit must be a non-empty string")
    elif not SHA1_RE.match(commit):
        errors.append("commit must be a lowercase 40-character SHA-1")

    sbom_format = data.get("format")
    if not _is_non_empty_string(sbom_format):
        errors.append("format must be a non-empty string")
    elif sbom_format not in VALID_FORMATS:
        errors.append("format must be one of: " + ", ".join(sorted(VALID_FORMATS)))

    components = data.get("components")
    if not isinstance(components, list) or not components:
        errors.append("components must be a non-empty list")
    else:
        for index, component in enumerate(components):
            prefix = f"components[{index}]"

            if not isinstance(component, dict):
                errors.append(f"{prefix} must be an object")
                continue

            name = component.get("name")
            if not _is_non_empty_string(name):
                errors.append(f"{prefix}.name must be a non-empty string")

            component_type = component.get("type")
            if not _is_non_empty_string(component_type):
                errors.append(f"{prefix}.type must be a non-empty string")
            elif component_type not in VALID_COMPONENT_TYPES:
                errors.append(
                    f"{prefix}.type must be one of: "
                    + ", ".join(sorted(VALID_COMPONENT_TYPES))
                )

            has_version = _is_non_empty_string(component.get("version"))
            has_version_status = _is_non_empty_string(component.get("version_status"))
            if not has_version and not has_version_status:
                errors.append(f"{prefix} must include either version or version_status")

            if "path" in component and not _is_safe_relative_path(component.get("path")):
                errors.append(f"{prefix}.path must be a safe repository-relative path")

    supply_chain_integrity_path = data.get("supply_chain_integrity_path")
    if not _is_safe_relative_path(supply_chain_integrity_path):
        errors.append("supply_chain_integrity_path must be a safe repository-relative path")

    release_evidence_bundle_path = data.get("release_evidence_bundle_path")
    if not _is_safe_relative_path(release_evidence_bundle_path):
        errors.append("release_evidence_bundle_path must be a safe repository-relative path")

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
        missing_evidence = sorted(REQUIRED_VALIDATION_EVIDENCE_KEYS - set(validation_evidence))
        for key in missing_evidence:
            errors.append(f"validation_evidence missing required key: {key}")

        validator_command = validation_evidence.get("validator_command")
        if not _is_non_empty_string(validator_command):
            errors.append("validation_evidence.validator_command must be non-empty")

        test_command = validation_evidence.get("test_command")
        if not _is_non_empty_string(test_command):
            errors.append("validation_evidence.test_command must be non-empty")

        if validation_evidence.get("validator_exit_code") != 0:
            errors.append("validation_evidence.validator_exit_code must be 0")

        if validation_evidence.get("test_exit_code") != 0:
            errors.append("validation_evidence.test_exit_code must be 0")

    return errors


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ASO-X SBOM artifact.")
    parser.add_argument(
        "artifact",
        nargs="?",
        default=str(DEFAULT_ARTIFACT),
        help=f"SBOM artifact path. Defaults to {DEFAULT_ARTIFACT}.",
    )
    args = parser.parse_args(argv)

    artifact_path = Path(args.artifact)
    result: dict[str, Any] = {
        "artifact": str(artifact_path),
        "errors": [],
        "ok": False,
    }

    try:
        data = load_json(artifact_path)
    except Exception as exc:  # pragma: no cover - exercised through CLI use
        result["errors"] = [f"failed to load artifact: {exc}"]
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    errors = validate_sbom_artifact(data)
    result["errors"] = errors
    result["ok"] = not errors

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())