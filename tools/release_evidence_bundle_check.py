from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_ARTIFACT = Path("docs/release/audit/sample-release-evidence-bundle.json")
SCHEMA_PREFIX = "aso-x.release_evidence_bundle."
REQUIRED_KEYS = {
    "schema_version",
    "bundle_id",
    "release_id",
    "branch",
    "commit",
    "generated_at_utc",
    "policy_document_path",
    "attestation_path",
    "audit_artifact_path",
    "test_evidence",
    "policy_audit_passed",
}
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
UTC_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_release_evidence_bundle(path: Path) -> list[str]:
    errors: list[str] = []

    if not path.exists():
        return [f"artifact not found: {path}"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid json: {exc}"]

    missing = sorted(REQUIRED_KEYS - set(data.keys()))
    if missing:
        errors.append("missing required keys: " + ", ".join(missing))

    schema_version = data.get("schema_version")
    if not _is_non_empty_string(schema_version) or not str(schema_version).startswith(SCHEMA_PREFIX):
        errors.append(f"schema_version must start with '{SCHEMA_PREFIX}'")

    for key in ("bundle_id", "release_id", "branch", "policy_document_path", "attestation_path", "audit_artifact_path"):
        if not _is_non_empty_string(data.get(key)):
            errors.append(f"{key} must be a non-empty string")

    commit = data.get("commit")
    if not _is_non_empty_string(commit) or not SHA1_RE.fullmatch(str(commit)):
        errors.append("commit must be a 40-character lowercase hexadecimal string")

    generated_at_utc = data.get("generated_at_utc")
    if not _is_non_empty_string(generated_at_utc) or not UTC_Z_RE.fullmatch(str(generated_at_utc)):
        errors.append("generated_at_utc must be an ISO-8601 UTC string ending in Z")

    policy_audit_passed = data.get("policy_audit_passed")
    if not isinstance(policy_audit_passed, bool):
        errors.append("policy_audit_passed must be boolean")

    test_evidence = data.get("test_evidence")
    if not isinstance(test_evidence, dict) or not test_evidence:
        errors.append("test_evidence must be a non-empty object")
    else:
        for key in ("validator_command", "test_command"):
            if not _is_non_empty_string(test_evidence.get(key)):
                errors.append(f"test_evidence.{key} must be a non-empty string")

        for key in ("validator_exit_code", "test_exit_code"):
            value = test_evidence.get(key)
            if not isinstance(value, int):
                errors.append(f"test_evidence.{key} must be an integer")
            elif value != 0:
                errors.append(f"test_evidence.{key} must equal 0")

    return errors


def build_report(path: Path) -> dict[str, object]:
    errors = validate_release_evidence_bundle(path)
    return {
        "ok": not errors,
        "artifact": str(path).replace("\\", "/"),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ASO-X release evidence bundle artifact.")
    parser.add_argument(
        "artifact",
        nargs="?",
        default=str(DEFAULT_ARTIFACT),
        help="Path to release evidence bundle artifact JSON.",
    )
    args = parser.parse_args(argv)

    path = Path(args.artifact)
    report = build_report(path)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())