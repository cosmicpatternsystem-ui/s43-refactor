import json
import sys
from pathlib import Path

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

def fail(message: str) -> None:
    print(f"ROADMAP_STATE_INVALID: {message}", file=sys.stderr)
    sys.exit(1)

if not STATE_PATH.exists():
    fail(f"missing {STATE_PATH}")

try:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8-sig"))
except Exception as exc:
    fail(f"invalid JSON: {exc}")

for field in required_fields:
    if field not in state:
        fail(f"missing required field: {field}")

if state["default_branch"] != "main":
    fail("default_branch must be main")

if str(state["current_phase"]) != "22.13":
    fail("current_phase must be 22.13")

if "phase22-12-baseline-verification-execution" in str(state.get("current_branch", "")):
    fail("current_branch still references stale Phase 22.12 branch")

if "Prepare Phase 22.12 baseline verification PR" in str(state.get("next_action", "")):
    fail("next_action still references stale Phase 22.12 PR preparation")

print("ROADMAP_STATE_VALID")