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

def test_missing_tasks_key_returns_insufficient_data():
    import importlib.util
    spec = importlib.util.spec_from_file_location("resolve_next_action", Path(__file__).parent / "resolve_next_action.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    result = mod.select_current({"phases": [{"id": "p1", "status": "in_progress"}]})
    assert result["status"] == "INSUFFICIENT_DATA"
    assert result["selection_reason"] == "tasks_key_invalid"


def test_tasks_not_a_list_returns_insufficient_data():
    import importlib.util
    spec = importlib.util.spec_from_file_location("resolve_next_action", Path(__file__).parent / "resolve_next_action.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    result = mod.select_current({"phases": [{"id": "p1", "status": "in_progress", "tasks": "bad"}]})
    assert result["status"] == "INSUFFICIENT_DATA"
    assert result["selection_reason"] == "tasks_key_invalid"


# --- PR #327: resolver coverage (legacy_id, pick tie-break, next_action chain, norm_scalar edges) ---
import importlib.util as _il, sys as _sys

def _load_resolver():
    spec = _il.spec_from_file_location(
        "scripts.resolve_next_action", "scripts/resolve_next_action.py"
    )
    mod = _il.module_from_spec(spec)
    _sys.modules["scripts.resolve_next_action"] = mod
    spec.loader.exec_module(mod)
    return mod

R = _load_resolver()


def test_entry_title_legacy_id_fallback():
    # legacy_id only wins when higher-priority keys are absent
    assert R.entry_title({"legacy_id": "P31-07"}) == "P31-07"
    # precedence: title/name/id before legacy_id
    assert R.entry_title({"id": "ID1", "legacy_id": "L1"}) == "ID1"
    # final fallback = file
    assert R.entry_title({"file": "x.py"}) == "x.py"
    # empty input
    assert R.entry_title({}) == ""


def test_pick_priority_and_tiebreak():
    # empty list -> None
    assert R.pick([]) is None
    # alphabetical tie-break on entry_title when other keys are equal
    same = [{"id": "b", "priority": "high"}, {"id": "a", "priority": "high"}]
    assert R.pick(same)["id"] == "a"
    # priority ordering, independent of exact mapping (uses module's own priority_rank)
    hi, lo = {"id": "hi", "priority": "high"}, {"id": "lo", "priority": "low"}
    winner = "hi" if R.priority_rank("high") <= R.priority_rank("low") else "lo"
    assert R.pick([lo, hi])["id"] == winner
    # items with _unresolved always sort last (first sort key)
    mixed = [{"id": "blocked", "priority": "high", "_unresolved": ["dep"]},
             {"id": "open", "priority": "low"}]
    assert R.pick(mixed)["id"] == "open"


def test_next_action_fallback_chain():
    base = lambda t: {"phases": [{"id": "P1", "status": "pending", "tasks": [t]}]}
    # explicit next_action wins
    r1 = R.select_current(base({"id": "T1", "status": "pending",
                                "next_action": "explicit", "description": "desc"}))
    assert r1["current_next_action"] == "explicit"
    # fallback to description
    r2 = R.select_current(base({"id": "T1", "status": "pending", "description": "do desc"}))
    assert r2["current_next_action"] == "do desc"
    # final fallback to task title
    r3 = R.select_current(base({"title": "Task Title", "status": "pending"}))
    assert r3["current_next_action"] == "Task Title"


def test_norm_scalar_edges():
    assert R.norm_scalar(None) == ""
    assert R.norm_scalar("") == ""
    assert isinstance(R.norm_scalar(123), str)
