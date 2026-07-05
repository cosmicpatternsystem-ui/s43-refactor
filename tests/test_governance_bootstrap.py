from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "AGENTS.md",
    "docs/PROJECT_STATE.md",
    "docs/ROADMAP.md",
    "docs/NEXT_ACTIONS.md",
    "docs/governance/GOVERNANCE_BASELINE.md",
    "docs/governance/LOCK_REGISTRY.json",
    "docs/governance/LOCK_SCHEMA.json",
    ".github/workflows/governance-enforcement.yml",
    "tests/test_governance_bootstrap.py",
    "tools/project_status.py",
]

def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

def test_required_files_exist():
    missing = [p for p in REQUIRED_FILES if not (ROOT / p).exists()]
    assert not missing, f"Missing required bootstrap artifacts: {missing}"

def test_agents_has_mandatory_sections():
    text = read_text("AGENTS.md")
    required = [
        "## Source of Truth",
        "## Mandatory First Read In Every New Session",
        "## Session Start Contract",
        "## Non-Negotiable Rules",
    ]
    for item in required:
        assert item in text, f"Missing AGENTS.md section: {item}"

def test_project_state_declares_self_discovery():
    text = read_text("docs/PROJECT_STATE.md")
    assert "self-discoverable" in text
    assert "without external explanation" in text

def test_roadmap_and_next_actions_exist_with_expected_markers():
    roadmap = read_text("docs/ROADMAP.md")
    nxt = read_text("docs/NEXT_ACTIONS.md")
    assert "## Strategic Objective" in roadmap
    assert "## Immediate Actions" in nxt

def test_governance_registry_is_valid_shape():
    data = json.loads(read_text("docs/governance/LOCK_REGISTRY.json"))
    assert data["project"] == "ASO-X"
    assert isinstance(data["locks"], list)
    assert len(data["locks"]) >= 12
    ids = [x["id"] for x in data["locks"]]
    assert len(ids) == len(set(ids)), "Duplicate lock ids found"

def test_governance_schema_exists():
    data = json.loads(read_text("docs/governance/LOCK_SCHEMA.json"))
    assert data["title"] == "ASO-X Governance Lock Registry"

def test_workflow_mentions_required_validation_targets():
    text = read_text(".github/workflows/governance-enforcement.yml")
    assert "project_status.py" in text
    assert "pytest" in text
    assert "LOCK_REGISTRY.json" in text

def test_status_tool_has_expected_output_markers():
    text = read_text("tools/project_status.py")
    for marker in [
        "Project: ASO-X",
        "Bootstrap:",
        "Source of truth: repository-only",
        "Governance locks declared:",
    ]:
        assert marker in text