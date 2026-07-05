import json
from pathlib import Path


REQUIRED_TOP_LEVEL_KEYS = [
    "schema_version",
    "release_id",
    "generated_at_utc",
    "branch",
    "commit",
    "policy_audit_passed",
    "checks",
    "approvers",
]


def validate_audit_artifact(path: Path) -> list[str]:
    errors: list[str] = []

    if not path.exists():
        return [f"missing artifact: {path.as_posix()}"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid json: {path.as_posix()}: {exc}"]

    if not isinstance(data, dict):
        return ["artifact root must be an object"]

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            errors.append(f"missing key: {key}")

    if errors:
        return errors

    schema_version = data["schema_version"]
    if not isinstance(schema_version, str) or not schema_version.startswith("aso-x.release_audit_trail."):
        errors.append("schema_version must start with 'aso-x.release_audit_trail.'")

    release_id = data["release_id"]
    if not isinstance(release_id, str) or not release_id.strip():
        errors.append("release_id must be a non-empty string")

    generated_at_utc = data["generated_at_utc"]
    if not isinstance(generated_at_utc, str) or not generated_at_utc.strip():
        errors.append("generated_at_utc must be a non-empty string")

    branch = data["branch"]
    if not isinstance(branch, str) or not branch.strip():
        errors.append("branch must be a non-empty string")

    commit = data["commit"]
    if not isinstance(commit, str) or not commit.strip():
        errors.append("commit must be a non-empty string")

    policy_audit_passed = data["policy_audit_passed"]
    if not isinstance(policy_audit_passed, bool):
        errors.append("policy_audit_passed must be boolean")

    checks = data["checks"]
    if not isinstance(checks, list) or not checks:
        errors.append("checks must be a non-empty array")
    else:
        for index, item in enumerate(checks):
            if not isinstance(item, dict):
                errors.append(f"checks[{index}] must be an object")
                continue

            name = item.get("name")
            status = item.get("status")

            if not isinstance(name, str) or not name.strip():
                errors.append(f"checks[{index}].name must be a non-empty string")

            if not isinstance(status, str) or not status.strip():
                errors.append(f"checks[{index}].status must be a non-empty string")

    approvers = data["approvers"]
    if not isinstance(approvers, list):
        errors.append("approvers must be an array")

    return errors


def main() -> int:
    artifact_path = Path("docs/release/audit/sample-release-audit.json")
    errors = validate_audit_artifact(artifact_path)

    payload = {
        "ok": not errors,
        "artifact": artifact_path.as_posix(),
        "errors": errors,
    }

    print(json.dumps(payload, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
