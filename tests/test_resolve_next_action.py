import json
import sys
import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[0]
CANDIDATES = [
    SCRIPT_PATH / "scripts" / "resolve_next_action.py",
    SCRIPT_PATH.parent / "scripts" / "resolve_next_action.py",
]


def load_module():
    for candidate in CANDIDATES:
        if candidate.exists():
            spec = importlib.util.spec_from_file_location(
                "scripts.resolve_next_action", str(candidate)
            )
            mod = importlib.util.module_from_spec(spec)
            sys.modules["scripts.resolve_next_action"] = mod
            spec.loader.exec_module(mod)
            return mod
    raise FileNotFoundError("scripts/resolve_next_action.py not found")


def run_resolver(roadmap_path):
    mod = load_module()
    data = json.loads(Path(roadmap_path).read_text(encoding="utf-8-sig"))
    return mod.select_current(data)


def make_roadmap(phases):
    return {"phases": phases}


def phase(pid, tasks, status="pending"):
    # No "title" key: entry_title() falls through to "id"
    return {"id": pid, "status": status, "tasks": tasks}


def task(tid, status="pending"):
    return {"id": tid, "status": status}


@pytest.fixture
def roadmap_file(tmp_path):
    return tmp_path / "roadmap.json"


def write(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def test_first_pending_task_selected(roadmap_file):
    write(roadmap_file, make_roadmap([phase("P1", [task("T1"), task("T2")])]))
    result = run_resolver(roadmap_file)
    assert result["status"] == "READY"
    assert result["current_task"] == "T1"
    assert result["selection_reason"] == "next_open_task"


def test_skips_completed_tasks(roadmap_file):
    write(roadmap_file, make_roadmap(
        [phase("P1", [task("T1", "complete"), task("T2")])]
    ))
    result = run_resolver(roadmap_file)
    assert result["current_task"] == "T2"


def test_all_complete_returns_complete(roadmap_file):
    write(roadmap_file, make_roadmap(
        [phase("P1", [task("T1", "complete")], "complete")]
    ))
    result = run_resolver(roadmap_file)
    assert result["status"] == "COMPLETE"
    assert result["selection_reason"] == "no_remaining_phases"


def test_task_order_preserved(roadmap_file):
    write(roadmap_file, make_roadmap([phase("P33-01", [
        task("TASK_33_01_01"),
        task("TASK_33_01_02"),
        task("TASK_33_01_03"),
    ])]))
    result = run_resolver(roadmap_file)
    assert result["current_task"] == "TASK_33_01_01"
def test_missing_tasks_key_returns_insufficient_data(tmp_path):
    p = tmp_path / "r.json"
    write(p, make_roadmap([{"id": "P1", "title": "Phase P1", "status": "pending"}]))
    result = run_resolver(p)
    assert result["status"] == "INSUFFICIENT_DATA"
    assert result["selection_reason"] == "tasks_key_invalid"

def test_tasks_not_a_list_returns_insufficient_data(tmp_path):
    p = tmp_path / "r.json"
    write(p, make_roadmap([{"id": "P1", "title": "Phase P1", "status": "pending", "tasks": "bad"}]))
    result = run_resolver(p)
    assert result["status"] == "INSUFFICIENT_DATA"
    assert result["selection_reason"] == "tasks_key_invalid"
