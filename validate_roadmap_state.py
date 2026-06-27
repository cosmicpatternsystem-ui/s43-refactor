import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

STATE_PATH = Path("ROADMAP/ROADMAP_STATE.json")

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
]


@dataclass(frozen=True)
class RoadmapStateContract:
    state_path: Path = STATE_PATH
    required_fields: tuple[str, ...] = tuple(required_fields)
    default_branch: str = "main"
    current_phase: str = "22.13"
    stale_branch_marker: str = "phase22-12-baseline-verification-execution"
    stale_next_action_marker: str = "Prepare Phase 22.12 baseline verification PR"


def validate_state_contract(state: dict[str, Any], contract: RoadmapStateContract) -> list[str]:
    errors: list[str] = []

    for field in contract.required_fields:
        if field not in state:
            errors.append(f"missing required field: {field}")

    if state.get("default_branch") != contract.default_branch:
        errors.append(f"default_branch must be {contract.default_branch}")

    if str(state.get("current_phase")) != contract.current_phase:
        errors.append(f"current_phase must be {contract.current_phase}")

    if contract.stale_branch_marker in str(state.get("current_branch", "")):
        errors.append("current_branch still references stale Phase 22.12 branch")

    if contract.stale_next_action_marker in str(state.get("next_action", "")):
        errors.append("next_action still references stale Phase 22.12 PR preparation")

    return errors


def load_state(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    contract = RoadmapStateContract()

    if not contract.state_path.exists():
        print(f"ROADMAP_STATE_INVALID: missing {contract.state_path}", file=sys.stderr)
        return 1

    try:
        state = load_state(contract.state_path)
    except Exception as exc:
        print(f"ROADMAP_STATE_INVALID: invalid JSON: {exc}", file=sys.stderr)
        return 1

    errors = validate_state_contract(state, contract)
    if errors:
        print("ROADMAP_STATE_INVALID:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("ROADMAP_STATE_VALID")
    return 0


if __name__ == "__main__":
    sys.exit(main())
