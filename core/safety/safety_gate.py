import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "runtime"
STATUS_PATH = RUNTIME / "safety_status.json"
POLICY_PATH = ROOT / "core" / "safety" / "policy.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def write_status(status, detail=None):
    RUNTIME.mkdir(parents=True, exist_ok=True)
    payload = {
        "project": "ASO",
        "component": "safety_gate",
        "status": status,
        "detail": detail or {},
        "updated_at": now(),
    }
    STATUS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def find_roadmap():
    candidates = [
        ROOT / "ROADMAP" / "master_plan.json",
        ROOT / "roadmap" / "master_plan.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("master_plan.json not found")


def load_policy():
    if not POLICY_PATH.exists():
        raise FileNotFoundError(f"policy not found: {POLICY_PATH}")
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def check_emergency_stop(policy):
    stop_file = ROOT / policy["hard_stops"]["emergency_stop_file"]
    if stop_file.exists():
        raise RuntimeError(f"EMERGENCY_STOP is active: {stop_file}")


def check_roadmap(policy):
    roadmap = find_roadmap()
    data = json.loads(roadmap.read_text(encoding="utf-8"))

    phases = data.get("phases")
    if not isinstance(phases, list):
        raise ValueError("roadmap phases must be a list")

    minimum = int(policy["hard_stops"].get("minimum_phases", 1))
    if len(phases) < minimum:
        raise ValueError(f"roadmap phase count below minimum: {len(phases)} < {minimum}")

    return roadmap, len(phases)


def main():
    try:
        policy = load_policy()
        check_emergency_stop(policy)
        roadmap, phase_count = check_roadmap(policy)

        detail = {
            "policy_version": policy.get("policy_version"),
            "mode": policy.get("mode"),
            "roadmap": str(roadmap),
            "phases": phase_count,
        }
        write_status("allowed", detail)
        print(json.dumps({"status": "allowed", "detail": detail}, indent=2))
        return 0

    except Exception as exc:
        detail = {"error": repr(exc)}
        write_status("blocked", detail)
        print(json.dumps({"status": "blocked", "detail": detail}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
