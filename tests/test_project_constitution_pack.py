from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_project_constitution_check_passes() -> None:
    result = subprocess.run(
        [sys.executable, "tools/project_constitution_check.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK: project constitution and autonomous governance layer validated" in result.stdout


def test_agent_entrypoint_rejects_chat_memory_as_source_of_truth() -> None:
    text = (ROOT / "AGENT_ENTRYPOINT.md").read_text(encoding="utf-8")
    assert "No project-critical decision may rely on chat memory" in text
    assert "Repository files outrank chat memory" not in text or "source of truth" in text.lower()


def test_roadmap_source_and_view_are_synchronized_by_ids() -> None:
    import re

    roadmap = (ROOT / "repo/roadmap/roadmap.yaml").read_text(encoding="utf-8")
    view = (ROOT / "docs/ROADMAP.md").read_text(encoding="utf-8")

    roadmap_ids = re.findall(r"^\s*-\s*id:\s*(R-\d{3})\s*$", roadmap, flags=re.MULTILINE)
    view_ids = re.findall(r"^##\s+(R-\d{3})\s+—", view, flags=re.MULTILINE)

    assert roadmap_ids == view_ids
    assert roadmap_ids == ["R-001", "R-002", "R-003", "R-004", "R-005", "R-006", "R-007", "R-008"]


def test_constitution_declares_commercial_and_durability_posture() -> None:
    text = (ROOT / "repo/contracts/PROJECT_CONSTITUTION.yaml").read_text(encoding="utf-8")
    assert "horizon_years: 50" in text
    assert "commercial_intent: private_and_enterprise" in text
    assert "anti_obsolescence_oriented" in text
    assert "agent_onboardable" in text
