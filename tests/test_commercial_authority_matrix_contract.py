from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MATRIX = ROOT / "docs" / "strategy" / "COMMERCIAL_AUTHORITY_MATRIX.md"
README = ROOT / "README.md"
GOV_INDEX = ROOT / "docs" / "governance" / "AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md"
GOV_MANIFEST = ROOT / "docs" / "governance" / "GOVERNANCE_DOCUMENTS_MANIFEST.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_commercial_authority_matrix_exists() -> None:
    assert MATRIX.exists(), "Commercial Authority Matrix must exist as a canonical strategy document."


def test_commercial_authority_matrix_required_sections() -> None:
    text = read(MATRIX)

    required_sections = [
        "# Commercial Authority Matrix",
        "## Purpose",
        "## Scope",
        "## Non-Negotiable Principles",
        "## Authority Levels",
        "### Level 0: Standard Commercial Motion",
        "### Level 1: Minor Commercial Exception",
        "### Level 2: Material Commercial Exception",
        "### Level 3: Strategic or High-Risk Commercial Exception",
        "## Discount Authority",
        "## Margin Floor",
        "## Payment Terms Authority",
        "## Contractual Concessions",
        "## Delivery Commitments",
        "## Security, Data, and Retention Commitments",
        "## NO-GO Conditions",
        "## Required Decision Record",
        "## Escalation Triggers",
        "## Enforcement",
        "## Relationship to Other Documents",
    ]

    for section in required_sections:
        assert section in text, f"Missing required section: {section}"


def test_commercial_authority_matrix_contains_hard_controls() -> None:
    text = read(MATRIX)

    required_terms = [
        "No commercial promise may bypass repo-governed policy.",
        "No discount may destroy the minimum acceptable margin floor.",
        "No verbal commercial exception is authoritative.",
        "Revenue does not override NO-GO conditions.",
        "An undocumented exception is not approved.",
        "Future changes to this matrix must be made through pull request review",
        "immutable Git history",
        "real-money resilience",
        "artifact retention",
    ]

    for term in required_terms:
        assert term in text, f"Missing required control language: {term}"


def test_commercial_authority_matrix_is_linked_from_readme() -> None:
    text = read(README)
    assert "Commercial Authority Matrix" in text
    assert "docs/strategy/COMMERCIAL_AUTHORITY_MATRIX.md" in text


def test_commercial_authority_matrix_is_linked_from_governance_index() -> None:
    text = read(GOV_INDEX)
    assert "Commercial Authority Matrix" in text
    assert "docs/strategy/COMMERCIAL_AUTHORITY_MATRIX.md" in text


def test_commercial_authority_matrix_is_linked_from_governance_manifest() -> None:
    text = read(GOV_MANIFEST)
    assert "Commercial Authority Matrix" in text
    assert "docs/strategy/COMMERCIAL_AUTHORITY_MATRIX.md" in text