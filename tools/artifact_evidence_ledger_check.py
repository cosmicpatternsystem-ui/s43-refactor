from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = REPO_ROOT / "docs" / "security" / "audit" / "artifact-retention-evidence-ledger.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_ledger_record(path: Path = LEDGER_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Ledger record not found: {path}")

    data = _load_json(path)

    required_top_level = [
        "schema_version",
        "record_type",
        "recorded_at_utc",
        "system",
        "repository",
        "branch",
        "commit_sha",
        "workflow",
        "policy",
        "evidence_inputs",
        "validators",
        "tests",
        "result",
        "retention_class",
        "durability_target",
    ]
    for key in required_top_level:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")

    if data["record_type"] != "artifact_retention_evidence_ledger":
        raise ValueError("record_type must be 'artifact_retention_evidence_ledger'")

    if data["system"] != "ASO-X":
        raise ValueError("system must be 'ASO-X'")

    if data["durability_target"] != "50y":
        raise ValueError("durability_target must be '50y'")

    workflow = data["workflow"]
    if not isinstance(workflow, dict):
        raise ValueError("workflow must be an object")

    triggers = workflow.get("triggers")
    if not isinstance(triggers, list):
        raise ValueError("workflow.triggers must be a list")

    for required_trigger in ("pull_request", "workflow_dispatch", "schedule"):
        if required_trigger not in triggers:
            raise ValueError(f"Missing workflow trigger in ledger: {required_trigger}")

    if workflow.get("schedule_cron") != "0 3 * * *":
        raise ValueError("workflow.schedule_cron must be '0 3 * * *'")

    policy = data["policy"]
    if not isinstance(policy, dict):
        raise ValueError("policy must be an object")

    policy_path = policy.get("path")
    if not isinstance(policy_path, str) or not policy_path:
        raise ValueError("policy.path must be a non-empty string")

    referenced_paths = []
    referenced_paths.append(Path(policy_path))
    referenced_paths.extend(Path(p) for p in data["evidence_inputs"])
    referenced_paths.extend(Path(p) for p in data["validators"])
    referenced_paths.extend(Path(p) for p in data["tests"])

    for rel_path in referenced_paths:
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            raise ValueError(f"Referenced path does not exist: {rel_path}")

    if data["result"] not in ("pass", "fail"):
        raise ValueError("result must be 'pass' or 'fail'")

    return data


def main() -> int:
    validate_ledger_record()
    print("artifact evidence ledger: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())