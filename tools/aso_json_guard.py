import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
BACKUPS = RUNTIME / "backups"
LOG_PATH = RUNTIME / "json_guard.log"

RUNTIME.mkdir(parents=True, exist_ok=True)
BACKUPS.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now(timezone.utc).isoformat()


def log(message):
    line = f"[{now()}] {message}"
    print(line)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def find_roadmap():
    candidates = [
        ROOT / "ROADMAP" / "master_plan.json",
        ROOT / "roadmap" / "master_plan.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("master_plan.json not found")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_payload(data):
    if not isinstance(data, dict):
        raise ValueError("roadmap root must be an object")

    phases = data.get("phases")
    if not isinstance(phases, list):
        raise ValueError("roadmap must contain a phases list")

    return len(phases)


def atomic_write_json(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def latest_backup_path():
    return BACKUPS / "master_plan.valid.json"


def timestamped_backup_path():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return BACKUPS / f"master_plan.valid.{stamp}.json"


def save_valid_backup(path, data):
    latest = latest_backup_path()
    atomic_write_json(latest, data)

    stamped = timestamped_backup_path()
    shutil.copyfile(latest, stamped)

    log(f"valid backup saved latest={latest} stamped={stamped}")


def restore_from_backup(path):
    backup = latest_backup_path()
    if not backup.exists():
        raise FileNotFoundError("roadmap is invalid and no valid backup exists")

    data = load_json(backup)
    phase_count = validate_payload(data)
    atomic_write_json(path, data)

    log(f"roadmap restored from backup path={backup} phases={phase_count}")
    return phase_count


def repair_or_validate():
    roadmap = find_roadmap()

    try:
        data = load_json(roadmap)
        phase_count = validate_payload(data)
        save_valid_backup(roadmap, data)
        log(f"roadmap valid path={roadmap} phases={phase_count}")
        return {
            "status": "valid",
            "path": str(roadmap),
            "phases": phase_count,
        }

    except Exception as exc:
        log(f"roadmap invalid path={roadmap} error={repr(exc)}")
        phase_count = restore_from_backup(roadmap)
        return {
            "status": "restored",
            "path": str(roadmap),
            "phases": phase_count,
            "error": repr(exc),
        }


def main():
    result = repair_or_validate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
