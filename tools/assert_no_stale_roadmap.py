import json
import sys
from pathlib import Path

FILES_TO_SCAN_TEXT = [
    "ROADMAP/ROADMAP_CANONICAL.md",
    "AUDIT/ROADMAP_CURRENT.md",
]

JSON_FILES = [
    "ROADMAP/ROADMAP_STATE.json",
    "AUDIT/ROADMAP_CURRENT.json",
]

FORBIDDEN_PATTERNS = [
    "phase22-12-baseline-verification-execution",
    "Prepare Phase 22.12 baseline verification PR",
    "phase22_12_status\": \"validation_complete",
    "current_phase\": \"22.12",
    "Current Phase: 22.12",
]

def fail(message: str) -> None:
    print(f"STALE_ROADMAP_DETECTED: {message}", file=sys.stderr)
    sys.exit(1)

for file_name in FILES_TO_SCAN_TEXT:
    path = Path(file_name)
    if not path.exists():
        fail(f"missing required roadmap file: {file_name}")
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in text:
            fail(f"{file_name} contains forbidden stale pattern: {pattern}")

for file_name in JSON_FILES:
    path = Path(file_name)
    if not path.exists():
        fail(f"missing required roadmap file: {file_name}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        fail(f"{file_name} invalid JSON: {exc}")

    current_phase = str(data.get("current_phase", ""))
    current_branch = str(data.get("current_branch", ""))
    next_action = str(data.get("next_action", ""))

    if current_phase == "22.12":
        fail(f"{file_name} current_phase is stale: {current_phase}")
    if "phase22-12-baseline-verification-execution" in current_branch:
        fail(f"{file_name} current_branch is stale: {current_branch}")
    if "Prepare Phase 22.12 baseline verification PR" in next_action:
        fail(f"{file_name} next_action is stale: {next_action}")

print("NO_STALE_ROADMAP_STATE")