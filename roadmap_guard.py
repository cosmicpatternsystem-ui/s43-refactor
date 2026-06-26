import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
CANDIDATES = [
    ROOT / "ROADMAP_CURRENT.json",
    ROOT / "AUDIT" / "ROADMAP_CURRENT.json",
]

REQUIRED_TOP = [
    "project",
    "roadmap_version",
    "schema_version",
    "authority",
    "lifecycle",
    "operational_metadata",
    "governance",
    "initiatives",
]

REQUIRED_LIFECYCLE = [
    "inception_date",
    "horizon_date",
    "last_updated",
    "roadmap_sync_status",
    "validation_status",
]

REQUIRED_OPERATIONAL = [
    "system_health",
]

REQUIRED_GOVERNANCE = [
    "immutable_storage",
]

ALLOWED_HEALTH = {"HEALTHY", "DEGRADED", "STALE", "PARTIAL_DATA"}

def fail(msg: str) -> int:
    print(f"[ROADMAP_GUARD][FAIL] {msg}")
    return 1

def ok(msg: str) -> None:
    print(f"[ROADMAP_GUARD][OK] {msg}")

def load_json_file(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def load_target():
    for p in CANDIDATES:
        if p.exists():
            return p, load_json_file(p)
    raise FileNotFoundError("No ROADMAP_CURRENT.json found in root or AUDIT directory")

def is_iso8601_utc(value: str) -> bool:
    try:
        if not isinstance(value, str):
            return False
        if value.endswith("Z"):
            datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
            return True
        return False
    except Exception:
        return False

def main() -> int:
    try:
        path, data = load_target()
    except Exception as e:
        return fail(str(e))

    for key in REQUIRED_TOP:
        if key not in data:
            return fail(f"missing top-level field: {key}")

    if data.get("project") != "ASO-X":
        return fail(f"project must be 'ASO-X', got: {data.get('project')}")

    schema_version = str(data.get("schema_version", ""))
    if not schema_version.startswith("2."):
        return fail(f"schema_version must start with '2.', got: {schema_version}")

    lifecycle = data.get("lifecycle")
    if not isinstance(lifecycle, dict):
        return fail("lifecycle must be an object")

    for key in REQUIRED_LIFECYCLE:
        if key not in lifecycle:
            return fail(f"missing lifecycle field: {key}")

    for key in ("inception_date", "horizon_date", "last_updated"):
        if not is_iso8601_utc(lifecycle.get(key)):
            return fail(f"lifecycle.{key} must be ISO-8601 UTC like 2026-06-26T12:50:00Z")

    operational = data.get("operational_metadata")
    if not isinstance(operational, dict):
        return fail("operational_metadata must be an object")
    for key in REQUIRED_OPERATIONAL:
        if key not in operational:
            return fail(f"missing operational_metadata field: {key}")

    if operational.get("system_health") not in ALLOWED_HEALTH:
        return fail(
            "operational_metadata.system_health must be one of: "
            + ", ".join(sorted(ALLOWED_HEALTH))
        )

    governance = data.get("governance")
    if not isinstance(governance, dict):
        return fail("governance must be an object")
    for key in REQUIRED_GOVERNANCE:
        if key not in governance:
            return fail(f"missing governance field: {key}")

    initiatives = data.get("initiatives")
    if not isinstance(initiatives, list) or len(initiatives) == 0:
        return fail("initiatives must be a non-empty list")

    ok(f"validated roadmap file: {path}")
    ok(f"roadmap_version={data.get('roadmap_version')}")
    ok(f"schema_version={data.get('schema_version')}")
    ok(f"system_health={operational.get('system_health')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())