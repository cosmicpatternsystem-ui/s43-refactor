from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_canonical_32_lock_registry():
    registry = json.loads((ROOT / "LOCK_REGISTRY.json").read_text(encoding="utf-8"))
    locks = registry["locks"]
    ids = [item["id"] for item in locks]
    assert registry["canonical_lock_count"] == 32
    assert len(locks) == 32
    assert len(set(ids)) == 32
    assert ids == [f"LOCK-{i:03d}" for i in range(1, 33)]

def test_required_continuity_artifacts_exist():
    required = [
        "GOVERNANCE_BASELINE.md",
        "PROJECT_STATE.md",
        "ROADMAP.md",
        "NEXT_ACTIONS.md",
        "DECISION_LOG.md",
        "POLICY_MATRIX.md",
        "OPERATING_MODEL.md",
        "REVENUE_MODEL.md",
        "asoctl.py",
        "tools/project_status.py",
        "tools/generate_next_actions.py",
    ]
    for path in required:
        assert (ROOT / path).exists(), path
