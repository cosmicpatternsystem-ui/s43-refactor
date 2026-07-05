#!/usr/bin/env python3
"""Validate ASO-X release attestation artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_ARTIFACT = Path("docs/release/audit/sample-release-attestation.json")
SCHEMA_PREFIX = "aso-x.release_attestation."

REQUIRED_KEYS = (
    "schema_version",
    "release_id",
    "attested_at_utc",
    "branch",
    "commit",
    "artifact_path",
    "artifact_sha256",
    "policy_audit_passed",
    "attestors",
)

_SHA1_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_attestation_artifact(path: Path) -> list[str]:
    """Return validation errors for a release attestation artifact."""
    errors: list[str] = []

    if not path.exists():
        return [f"artifact does not exist: {path}"]

    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [f"invalid utf-8: {path}: {exc}"]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [f"invalid json: {path}: {exc}"]

    if not isinstance(data, dict):
        return ["artifact must be a JSON object"]

    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"missing required key: {key}")

    if errors:
        return errors

    schema_version = data["schema_version"]
    if not _is_non_empty_string(schema_version):
        errors.append("schema_version must be a non-empty string")
    elif not schema_version.startswith(SCHEMA_PREFIX):
        errors.append(f"schema_version must start with {SCHEMA_PREFIX!r}")

    release_id = data["release_id"]
    if not _is_non_empty_string(release_id):
        errors.append("release_id must be a non-empty string")

    attested_at_utc = data["attested_at_utc"]
    if not _is_non_empty_string(attested_at_utc):
        errors.append("attested_at_utc must be a non-empty string")
    elif not attested_at_utc.endswith("Z"):
        errors.append("attested_at_utc must end with 'Z'")

    branch = data["branch"]
    if not _is_non_empty_string(branch):
        errors.append("branch must be a non-empty string")

    commit = data["commit"]
    if not isinstance(commit, str):
        errors.append("commit must be a string")
    elif not _SHA1_RE.match(commit):
        errors.append("commit must be a 40-character hexadecimal SHA-1 value")

    artifact_path = data["artifact_path"]
    if not _is_non_empty_string(artifact_path):
        errors.append("artifact_path must be a non-empty string")

    artifact_sha256 = data["artifact_sha256"]
    if not isinstance(artifact_sha256, str):
        errors.append("artifact_sha256 must be a string")
    elif not _SHA256_RE.match(artifact_sha256):
        errors.append("artifact_sha256 must be a 64-character hexadecimal SHA-256 value")

    policy_audit_passed = data["policy_audit_passed"]
    if not isinstance(policy_audit_passed, bool):
        errors.append("policy_audit_passed must be a boolean")

    attestors = data["attestors"]
    if not isinstance(attestors, list):
        errors.append("attestors must be an array")
    elif not attestors:
        errors.append("attestors must be a non-empty array")
    else:
        for index, attestor in enumerate(attestors):
            if not _is_non_empty_string(attestor):
                errors.append(f"attestors[{index}] must be a non-empty string")

    return errors


def build_report(path: Path) -> dict[str, Any]:
    errors = validate_attestation_artifact(path)
    return {
        "ok": not errors,
        "artifact": str(path).replace("\\", "/"),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate an ASO-X release attestation artifact."
    )
    parser.add_argument(
        "artifact",
        nargs="?",
        default=str(DEFAULT_ARTIFACT),
        help=f"Artifact path to validate. Defaults to {DEFAULT_ARTIFACT}.",
    )

    args = parser.parse_args(argv)
    path = Path(args.artifact)

    report = build_report(path)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
