from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROADMAP_ID_PATTERN = re.compile(r"\bP\d-[A-Z0-9-]+\b")


def extract_roadmap_ids(value: object) -> list[str]:
    ids: list[str] = []

    def collect(candidate: object) -> None:
        if isinstance(candidate, str) and ROADMAP_ID_PATTERN.fullmatch(candidate):
            ids.append(candidate)

    def visit(node: object) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                collect(key)
                visit(child)
            return
        if isinstance(node, list):
            for child in node:
                visit(child)
            return
        collect(node)

    visit(value)

    unique_ids: list[str] = []
    for item in ids:
        if item not in unique_ids:
            unique_ids.append(item)
    return unique_ids


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
    assert "source of truth" in text.lower()


def test_roadmap_source_and_view_are_synchronized_by_ids() -> None:
    roadmap = json.loads(
        (ROOT / "docs/governance/ROADMAP_CURRENT.json").read_text(encoding="utf-8")
    )
    view = (ROOT / "docs/governance/ROADMAP_CANONICAL.md").read_text(encoding="utf-8")

    roadmap_ids = extract_roadmap_ids(roadmap)

    view_ids = ROADMAP_ID_PATTERN.findall(view)
    view_unique: list[str] = []
    for item in view_ids:
        if item not in view_unique:
            view_unique.append(item)

    assert roadmap_ids
    assert view_unique

    missing_ids = [item for item in view_unique if item not in roadmap_ids]
    assert missing_ids == []
    assert "P0-ROADMAP-AUTHORITY" in roadmap_ids
    assert "P2-COMMERCIAL-VALIDATION" in roadmap_ids


def test_constitution_declares_commercial_and_durability_posture() -> None:
    text = (ROOT / "repo/contracts/PROJECT_CONSTITUTION.yaml").read_text(encoding="utf-8")
    assert "horizon_years: 50" in text
    assert "commercial_intent: private_and_enterprise" in text
    assert "anti_obsolescence_oriented" in text
    assert "agent_onboardable" in text
