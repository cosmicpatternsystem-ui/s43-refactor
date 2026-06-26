import json
import sys
from pathlib import Path
from datetime import datetime

STATE_PATH = Path("ROADMAP/ROADMAP_STATE.json")

REQUIRED_FIELDS = [
    "schema_version",
    "project",
    "roadmap_version",
    "default_branch",
    "current_phase",
    "current_branch",
    "phase_title",
    "previous_phase",
    "roadmap_sync_status",
    "validation_status",
    "state_type",
    "system_health",
    "authority",
    "source_of_truth",
    "next_action",
    "updated_at",
]

ALLOWED_SYNC_STATUS = {"synced", "pending", "out_of_sync", "failed"}
ALLOWED_HEALTH = {"HEALTHY", "DEGRADED", "STALE", "PARTIAL_DATA"}


def warn(rule: str, message: str) -> None:
    print(f"[ROADMAP_STATE][WARN][{rule}] {message}")


def fail(rule: str, message: str) -> int:
    print(f"[ROADMAP_STATE][FAIL][{rule}] {message}")
    return 1


def ok(message: str) -> None:
    print(f"[ROADMAP_STATE][OK] {message}")


def load_state(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def is_iso8601_utc(value: str) -> bool:
    if not isinstance(value, str):
        return False
    try:
        if not value.endswith("Z"):
            return False
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except Exception:
        return False


def main() -> int:
    if not STATE_PATH.exists():
        return fail("RULE_RS_001", f"Missing roadmap state file: {STATE_PATH}")

    try:
        state = load_state(STATE_PATH)
    except Exception as exc:
        return fail("RULE_RS_002", f"Invalid JSON or encoding: {exc}")

    for field in REQUIRED_FIELDS:
        if field not in state:
            return fail("RULE_RS_003", f"Missing required field: {field}")

    if state.get("project") != "ASO-X":
        return fail("RULE_RS_008", f"project must be 'ASO-X', got '{state.get('project')}'")

    sync_status = state.get("roadmap_sync_status")
    if sync_status not in ALLOWED_SYNC_STATUS:
        return fail(
            "RULE_RS_009",
            f"Non-canonical roadmap_sync_status '{sync_status}'. Allowed: {sorted(ALLOWED_SYNC_STATUS)}",
        )

    schema_version = str(state.get("schema_version", ""))
    if not schema_version.startswith("2."):
        return fail(
            "RULE_RS_011",
            f"schema_version '{schema_version}' is not compatible with expected 2.x contract",
        )

    health = state.get("system_health")
    if health not in ALLOWED_HEALTH:
        return fail(
            "RULE_RS_012",
            f"system_health '{health}' is not canonical. Allowed: {sorted(ALLOWED_HEALTH)}",
        )

    if not is_iso8601_utc(state.get("updated_at")):
        return fail("RULE_RS_013", "updated_at must be ISO-8601 UTC like 2026-06-26T12:50:00Z")

    if state.get("source_of_truth") != "runtime/state/project_memory.sqlite":
        warn(
            "RULE_RS_014",
            "source_of_truth is not runtime/state/project_memory.sqlite; JSON may be compatibility-only",
        )

    ok("Runtime roadmap state validated")
    ok(f"project={state.get('project')}")
    ok(f"schema_version={state.get('schema_version')}")
    ok(f"roadmap_sync_status={state.get('roadmap_sync_status')}")
    ok(f"system_health={state.get('system_health')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())