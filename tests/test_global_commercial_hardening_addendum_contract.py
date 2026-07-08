from pathlib import Path


def test_global_commercial_hardening_addendum_exists():
    path = Path("docs/strategy/GLOBAL_COMMERCIAL_HARDENING_ADDENDUM.md")
    assert path.exists(), "Global commercial hardening addendum must exist."


def test_global_commercial_hardening_addendum_has_required_sections():
    path = Path("docs/strategy/GLOBAL_COMMERCIAL_HARDENING_ADDENDUM.md")
    text = path.read_text(encoding="utf-8")
    required = [
        "# Global Commercial Hardening Addendum",
        "## Purpose",
        "## Core Commercial Hardening Principles",
        "## Non-Negotiable Controls",
        "## Decision Gates",
        "## Operating Requirements",
        "## Failure Conditions",
        "## Enforcement Posture",
    ]
    for item in required:
        assert item in text, f"Missing section: {item}"


def test_global_commercial_hardening_addendum_is_linked_in_readme():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "GLOBAL_COMMERCIAL_HARDENING_ADDENDUM.md" in text


def test_global_commercial_hardening_addendum_is_linked_in_governance_index():
    text = Path(
        "docs/governance/AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md"
    ).read_text(encoding="utf-8")
    assert "GLOBAL_COMMERCIAL_HARDENING_ADDENDUM.md" in text


def test_global_commercial_hardening_addendum_is_listed_in_manifest():
    text = Path(
        "docs/governance/GOVERNANCE_DOCUMENTS_MANIFEST.md"
    ).read_text(encoding="utf-8")
    assert "GLOBAL_COMMERCIAL_HARDENING_ADDENDUM.md" in text