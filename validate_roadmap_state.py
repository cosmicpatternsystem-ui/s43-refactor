from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STATE_PATH = Path("ROADMAP/ROADMAP_STATE.json")


@dataclass(frozen=True)
class RoadmapStateContract:
    project: str = "ASO-X"
    schema_version: str = "2.1.0"
    default_branch: str = "main"
    stale_next_action_marker: str = "Phase 22.12 PR preparation"


required_fields = [
    "schema_version",
    "project",
    "default_branch",
    "current_phase",
    "current_branch",
    "phase_title",
    "previous_phase",
    "roadmap_sync_status",
    "next_action",
    "updated_at",
    "continuity_contract",
]


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def load_state(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_state_contract(
    state: dict[str, Any], contract: RoadmapStateContract
) -> list[str]:
    errors: list[str] = []

    for field in required_fields:
        if field not in state:
            errors.append(f"missing required field: {field}")

    if state.get("project") != contract.project:
        errors.append(f"project must be {contract.project}")

    if state.get("schema_version") != contract.schema_version:
        errors.append(f"schema_version must be {contract.schema_version}")

    if state.get("default_branch") != contract.default_branch:
        errors.append(f"default_branch must be {contract.default_branch}")

    if contract.stale_next_action_marker in str(state.get("next_action", "")):
        errors.append("next_action still references stale Phase 22.12 PR preparation")

    continuity = state.get("continuity_contract")
    if not isinstance(continuity, dict):
        errors.append("continuity_contract must be an object")
        return errors

    expected_flags = {
        "baseline_commit": "0ad415a",
        "resume_source": "latest_clean_git_head",
        "repository_is_authoritative": True,
        "checkpoint_required": True,
        "preflight_required": True,
        "post_validation_required": True,
        "local_commit_required": True,
        "push_when_remote_available": True,
        "dirty_tree_blocks_automation": True,
        "restart_recovery_source": "repository_validation_only",
    }

    for key, expected in expected_flags.items():
        if continuity.get(key) != expected:
            errors.append(f"continuity_contract.{key} must be {expected!r}")

    return errors


def main() -> int:
    try:
        state = load_state(STATE_PATH)
    except FileNotFoundError:
        return fail(f"ROADMAP_STATE_MISSING: {STATE_PATH}")
    except json.JSONDecodeError as exc:
        return fail(f"ROADMAP_STATE_INVALID_JSON: {exc}")

    errors = validate_state_contract(state, RoadmapStateContract())
    if errors:
        for error in errors:
            print(f"ROADMAP_STATE_ERROR: {error}", file=sys.stderr)
        return 1

    print("ROADMAP_STATE_VALID")
    return 0


if __name__ == "__main__":
    sys.exit(main())
