from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DEFAULT_ARTIFACT = Path("docs/security/audit/sample-supply-chain-integrity.json")
SCHEMA_PREFIX = "aso-x.supply_chain_integrity."
REQUIRED_KEYS = {
    "schema_version",
    "artifact_id",
    "generated_at_utc",
    "source_repository",
    "branch",
    "commit",
    "policy_document_path",
    "release_evidence_bundle_path",
    "tracked_dependency_files",
    "dependency_lockfiles_present",
    "network_free_validation",
    "mutable_external_sources_allowed",
    "validation_evidence",
    "policy_audit_passed",
}
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
UTC_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_repo_relative_path(value: object) -> bool:
    if not _is_non_empty_string(value):
        return False

    path = str(value).strip()
    normalized = path.replace("\\", "/")

    if normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized:
        return False
    if normalized in {".", ".."}:
        return False
    if ":" in normalized:
        return False

    return True


def validate_supply_chain_integrity(path: Path) -> list[str]:
    errors: list[str] = []

    if not path.exists():
        return [f"artifact not found: {path}"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid json: {exc}"]

    if not isinstance(data, dict):
        return ["artifact must be a JSON object"]

    missing = sorted(REQUIRED_KEYS - set(data.keys()))
    if missing:
        errors.append("missing required keys: " + ", ".join(missing))

    schema_version = data.get("schema_version")
    if not _is_non_empty_string(schema_version) or not str(schema_version).startswith(SCHEMA_PREFIX):
        errors.append(f"schema_version must start with '{SCHEMA_PREFIX}'")

    for key in ("artifact_id", "source_repository", "branch"):
        if not _is_non_empty_string(data.get(key)):
            errors.append(f"{key} must be a non-empty string")

    generated_at_utc = data.get("generated_at_utc")
    if not _is_non_empty_string(generated_at_utc) or not UTC_Z_RE.fullmatch(str(generated_at_utc)):
        errors.append("generated_at_utc must be an ISO-8601 UTC string ending in Z")

    commit = data.get("commit")
    if not _is_non_empty_string(commit) or not SHA1_RE.fullmatch(str(commit)):
        errors.append("commit must be a 40-character lowercase hexadecimal string")

    for key in ("policy_document_path", "release_evidence_bundle_path"):
        if not _is_repo_relative_path(data.get(key)):
            errors.append(f"{key} must be a repository-relative path string")

    tracked_dependency_files = data.get("tracked_dependency_files")
    if not isinstance(tracked_dependency_files, list) or not tracked_dependency_files:
        errors.append("tracked_dependency_files must be a non-empty list")
    else:
        for index, item in enumerate(tracked_dependency_files):
            if not _is_repo_relative_path(item):
                errors.append(f"tracked_dependency_files[{index}] must be a repository-relative path string")

    dependency_lockfiles_present = data.get("dependency_lockfiles_present")
    if not isinstance(dependency_lockfiles_present, bool):
        errors.append("dependency_lockfiles_present must be boolean")
    elif dependency_lockfiles_present is not True:
        errors.append("dependency_lockfiles_present must be true")

    network_free_validation = data.get("network_free_validation")
    if not isinstance(network_free_validation, bool):
        errors.append("network_free_validation must be boolean")
    elif network_free_validation is not True:
        errors.append("network_free_validation must be true")

    mutable_external_sources_allowed = data.get("mutable_external_sources_allowed")
    if not isinstance(mutable_external_sources_allowed, bool):
        errors.append("mutable_external_sources_allowed must be boolean")
    elif mutable_external_sources_allowed is not False:
        errors.append("mutable_external_sources_allowed must be false")

    policy_audit_passed = data.get("policy_audit_passed")
    if not isinstance(policy_audit_passed, bool):
        errors.append("policy_audit_passed must be boolean")
    elif policy_audit_passed is not True:
        errors.append("policy_audit_passed must be true")

    validation_evidence = data.get("validation_evidence")
    if not isinstance(validation_evidence, dict) or not validation_evidence:
        errors.append("validation_evidence must be a non-empty object")
    else:
        for key in ("validator_command", "test_command"):
            if not _is_non_empty_string(validation_evidence.get(key)):
                errors.append(f"validation_evidence.{key} must be a non-empty string")

        for key in ("validator_exit_code", "test_exit_code"):
            value = validation_evidence.get(key)
            if not isinstance(value, int):
                errors.append(f"validation_evidence.{key} must be an integer")
            elif value != 0:
                errors.append(f"validation_evidence.{key} must equal 0")

    return errors


def build_report(path: Path) -> dict[str, object]:
    errors = validate_supply_chain_integrity(path)
    return {
        "ok": not errors,
        "artifact": str(path).replace("\\", "/"),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ASO-X supply chain integrity artifact.")
    parser.add_argument(
        "artifact",
        nargs="?",
        default=str(DEFAULT_ARTIFACT),
        help="Path to supply chain integrity artifact JSON.",
    )
    args = parser.parse_args(argv)

    report = build_report(Path(args.artifact))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())