import json
import sys
import importlib.util
from pathlib import Path

import pytest

RESOLVER = "scripts/resolve_next_action.py"


def run_resolver(roadmap_path):
    spec = importlib.util.spec_from_file_location(
        "scripts.resolve_next_action", RESOLVER
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["scripts.resolve_next_action"] = mod
    spec.loader.exec_module(mod)
    data = json.loads(Path(roadmap_path).read_text(encoding="utf-8"))
    return mod.select_current(data)


def make_roadmap(phases):
    return {"phases": phases}


def phase(pid, tasks, status="pending"):
    # id و title یکسان تا با entry_title سازگار بماند
    return {"id": pid, "title": pid, "status": status, "tasks": tasks}


def task(tid, status="pending"):
    return {"id": tid, "title": tid, "status": status}


def write(path, data):
    Path(path).write_text(json.dumps(data), encoding="utf-8")


@pytest.fixture
def mock_roadmap(tmp_path):
    return tmp_path / "roadmap.json"


def test_first_pending_task_selected(mock_roadmap):
    write(mock_roadmap, make_roadmap([phase("P1", [task("T1"), task("T2")])]))
    result = run_resolver(mock_roadmap)
    assert result["status"] == "READY"
    assert result["current_task"] == "T1"
    assert result["selection_reason"] == "next_open_task"


def test_skips_completed_tasks(mock_roadmap):
    write(mock_roadmap, make_roadmap([phase("P1", [task("T1", "complete"), task("T2")])]))
    result = run_resolver(mock_roadmap)
    assert result["status"] == "READY"
    assert result["current_task"] == "T2"


def test_all_complete_returns_complete(mock_roadmap):
    write(mock_roadmap, make_roadmap([phase("P1", [task("T1", "complete")], "complete")]))
    result = run_resolver(mock_roadmap)
    assert result["status"] == "COMPLETE"
    assert result["current_task"] == ""
    assert result["selection_reason"] == "no_remaining_phases"


def test_task_order_preserved(mock_roadmap):
    write(mock_roadmap, make_roadmap([phase("P33-01", [
        task("TASK_33_01_01"),
        task("TASK_33_01_02"),
        task("TASK_33_01_03"),
    ])]))
    result = run_resolver(mock_roadmap)
    assert result["current_task"] == "TASK_33_01_01"