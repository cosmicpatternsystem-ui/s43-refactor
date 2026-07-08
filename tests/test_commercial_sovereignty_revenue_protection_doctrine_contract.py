from pathlib import Path


DOC = Path("docs/strategy/COMMERCIAL_SOVEREIGNTY_REVENUE_PROTECTION_DOCTRINE.md")


def test_commercial_sovereignty_revenue_protection_doctrine_exists() -> None:
    assert DOC.exists(), f"Missing doctrine document: {DOC}"


def test_commercial_sovereignty_revenue_protection_doctrine_has_required_sections() -> None:
    text = DOC.read_text(encoding="utf-8")
    required_phrases = [
        "# Commercial Sovereignty & Revenue Protection Doctrine",
        "## Core Doctrine",
        "## Mandatory control gates",
        "## Required decision record",
        "## Prohibited patterns",
        "## Relationship to other governance artifacts",
        "## Acceptance criteria",
        "collectible, margin-safe, contractually bounded, operationally supportable, and durably auditable",
        "Commercial acceptance must conform to the commercial authority matrix",
        "Any exception to policy, pricing, terms, commitments, or support posture must be time-bounded",
    ]
    for phrase in required_phrases:
        assert phrase in text, f"Missing required doctrine phrase: {phrase}"


def test_commercial_sovereignty_revenue_protection_doctrine_references_parented_artifacts() -> None:
    text = DOC.read_text(encoding="utf-8")
    required_links = [
        "docs/strategy/COMMERCIAL_AUTHORITY_MATRIX.md",
        "docs/strategy/COMMERCIAL_CONTROLS_ENFORCEMENT_PACK.md",
        "docs/strategy/GLOBAL_COMMERCIAL_RESILIENCE_FRAMEWORK.md",
    ]
    for link in required_links:
        assert link in text, f"Missing governed artifact reference: {link}"


def test_commercial_sovereignty_revenue_protection_doctrine_is_linked_from_readme() -> None:
    text = Path("README.md").read_text(encoding="utf-8")
    assert "COMMERCIAL_SOVEREIGNTY_REVENUE_PROTECTION_DOCTRINE.md" in text


def test_commercial_sovereignty_revenue_protection_doctrine_is_linked_from_governance_index() -> None:
    text = Path("docs/governance/AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md").read_text(encoding="utf-8")
    assert "COMMERCIAL_SOVEREIGNTY_REVENUE_PROTECTION_DOCTRINE.md" in text


def test_commercial_sovereignty_revenue_protection_doctrine_is_linked_from_governance_manifest() -> None:
    text = Path("docs/governance/GOVERNANCE_DOCUMENTS_MANIFEST.md").read_text(encoding="utf-8")
    assert "COMMERCIAL_SOVEREIGNTY_REVENUE_PROTECTION_DOCTRINE.md" in text