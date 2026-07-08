from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def test_readme_links_autonomous_governance_operations_index():
    text = README.read_text(encoding="utf-8")
    assert "docs/governance/AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md" in text


def test_readme_keeps_governance_entrypoint_heading():
    text = README.read_text(encoding="utf-8")
    assert "## Autonomous Governance Operations" in text or "## Governance" in text