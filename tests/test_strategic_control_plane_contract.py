from pathlib import Path

README = Path("README.md")
GOV_INDEX = Path("docs/governance/AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md")
MANIFEST = Path("docs/governance/GOVERNANCE_DOCUMENTS_MANIFEST.md")
STRATEGIC_CONTROL = Path("docs/strategy/STRATEGIC_CONTROL_PLANE.md")

STRATEGIC_DOCS = [
    Path("docs/strategy/PROJECT_OBJECTIVES.md"),
    Path("docs/strategy/CANONICAL_ROADMAP.md"),
    Path("docs/strategy/FIFTY_YEAR_DURABILITY_DOCTRINE.md"),
    Path("docs/strategy/MONETIZATION_AND_MARKET_DOCTRINE.md"),
    Path("docs/strategy/AUTONOMOUS_CONTINUITY_GUIDE.md"),
    Path("docs/strategy/ANTI_OBSOLESCENCE_POLICY.md"),
    Path("docs/strategy/PORTABILITY_AND_PLATFORM_INDEPENDENCE.md"),
    Path("docs/strategy/PRODUCT_IDENTITY_AND_DIFFERENTIATION.md"),
]

KEYWORDS = {
    "docs/strategy/STRATEGIC_CONTROL_PLANE.md": [
        "canonical",
        "source of truth",
        "repository",
        "autonomous",
        "durability",
        "monetization",
        "platform independence",
    ],
    "docs/strategy/PROJECT_OBJECTIVES.md": [
        "repository",
        "source of truth",
        "enterprise",
        "50-year",
        "autonomous",
        "commercial",
    ],
    "docs/strategy/CANONICAL_ROADMAP.md": [
        "canonical roadmap",
        "Horizon 0",
        "Horizon 9",
        "commercialization",
        "50-year",
    ],
    "docs/strategy/FIFTY_YEAR_DURABILITY_DOCTRINE.md": [
        "50-year",
        "source of truth",
        "Plain text",
        "BOM-free UTF-8 LF",
        "deterministic",
    ],
    "docs/strategy/MONETIZATION_AND_MARKET_DOCTRINE.md": [
        "monetization",
        "commercial",
        "enterprise",
        "private",
        "strategic value",
    ],
    "docs/strategy/AUTONOMOUS_CONTINUITY_GUIDE.md": [
        "README.md",
        "source of truth",
        "autonomous agent",
        "pull requests",
        "validation",
    ],
    "docs/strategy/ANTI_OBSOLESCENCE_POLICY.md": [
        "chat transcripts",
        "canonical control planes",
        "replaceable",
        "lock-in",
        "Silent drift",
    ],
    "docs/strategy/PORTABILITY_AND_PLATFORM_INDEPENDENCE.md": [
        "Windows",
        "Linux",
        "macOS",
        "cp1252-safe stdout",
        "BOM-free UTF-8 LF",
    ],
    "docs/strategy/PRODUCT_IDENTITY_AND_DIFFERENTIATION.md": [
        "governance",
        "artifact retention",
        "extensible",
        "enterprise-grade",
        "commercial value",
    ],
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_readme_links_strategic_control_plane() -> None:
    assert "docs/strategy/STRATEGIC_CONTROL_PLANE.md" in _read(README)


def test_governance_index_links_strategic_control_plane() -> None:
    text = _read(GOV_INDEX)
    assert "docs/strategy/STRATEGIC_CONTROL_PLANE.md" in text
    assert "canonical" in text.lower()


def test_manifest_lists_strategic_documents() -> None:
    text = _read(MANIFEST)
    for path in [STRATEGIC_CONTROL, *STRATEGIC_DOCS]:
        assert path.as_posix() in text


def test_strategic_control_plane_links_all_strategic_documents() -> None:
    text = _read(STRATEGIC_CONTROL)
    for path in STRATEGIC_DOCS:
        assert path.name in text


def test_strategic_documents_exist_and_are_not_empty() -> None:
    for path in [STRATEGIC_CONTROL, *STRATEGIC_DOCS]:
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip()


def test_strategic_documents_contain_required_keywords() -> None:
    for raw_path, keywords in KEYWORDS.items():
        text = _read(Path(raw_path))
        lowered = text.lower()
        for keyword in keywords:
            assert keyword.lower() in lowered, f"{raw_path} missing keyword: {keyword}"
