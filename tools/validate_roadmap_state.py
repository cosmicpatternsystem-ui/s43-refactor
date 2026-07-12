import json
import sys
from pathlib import Path

STATE_PATH = Path("ROADMAP_CURRENT.json")

REQUIRED_TOP_LEVEL_FIELDS = [
    "schema_version",
    "source_of_truth",
    "canonical_roadmap",
    "phases",
    "phase_count",
    "enforcement_model",
    "operational_metadata_schema",
    "generated_by",
    "updated_at_utc",
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

for field in REQUIRED_TOP_LEVEL_FIELDS:
    if field not in state:
        fail(f"missing required field: {field}")

if not state["source_of_truth"]:
    fail("source_of_truth must not be empty")

if not state["canonical_roadmap"]:
    fail("canonical_roadmap must not be empty")

if not isinstance(state["phases"], list):
    fail("phases must be a list")

if not isinstance(state["phase_count"], int):
    fail("phase_count must be an integer")

if state["phase_count"] != len(state["phases"]):
    fail("phase_count must match phases length")

print("ROADMAP_STATE_VALID")