from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_top_level_commercial_doctrine_exists():
    path = ROOT / "docs" / "strategy" / "TOP_LEVEL_COMMERCIAL_OPERATING_DOCTRINE.md"
    assert path.exists(), "Top-level commercial doctrine must exist"


def test_top_level_commercial_doctrine_contains_required_sections():
    path = ROOT / "docs" / "strategy" / "TOP_LEVEL_COMMERCIAL_OPERATING_DOCTRINE.md"
    text = path.read_text(encoding="utf-8")
    required = [
        "# TOP-LEVEL COMMERCIAL OPERATING DOCTRINE",
        "## Commercial Identity",
        "## Core Commercial Thesis",
        "## Revenue Quality Principle",
        "## Strategic Market Position",
        "## Ideal Customer Profile",
        "## Offer Architecture",
        "## Pricing Doctrine",
        "## Contracting Discipline",
        "## Roadmap Governance",
        "## Customer Selection Discipline",
        "## Sales Conduct Doctrine",
        "## Trust as a Commercial Asset",
        "## Anti-Fragility Principle",
        "## Retention and Expansion Principle",
        "## Autonomy Boundaries",
        "## Portability and Lock-In Doctrine",
        "## Executive Decision Standard",
        "## Final Rule",
    ]
    for item in required:
        assert item in text, f"Missing required section: {item}"


def test_readme_references_top_level_commercial_doctrine():
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    assert "docs/strategy/TOP_LEVEL_COMMERCIAL_OPERATING_DOCTRINE.md" in text


def test_governance_index_references_top_level_commercial_doctrine():
    path = ROOT / "docs" / "governance" / "AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md"
    text = path.read_text(encoding="utf-8")
    assert "docs/strategy/TOP_LEVEL_COMMERCIAL_OPERATING_DOCTRINE.md" in text


def test_governance_manifest_references_top_level_commercial_doctrine():
    path = ROOT / "docs" / "governance" / "GOVERNANCE_DOCUMENTS_MANIFEST.md"
    text = path.read_text(encoding="utf-8")
    assert "docs/strategy/TOP_LEVEL_COMMERCIAL_OPERATING_DOCTRINE.md" in text