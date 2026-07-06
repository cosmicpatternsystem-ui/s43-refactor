from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

README = REPO_ROOT / "README.md"
INDEX = REPO_ROOT / "docs/governance/AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md"
MANIFEST = REPO_ROOT / "docs/governance/GOVERNANCE_DOCUMENTS_MANIFEST.md"

CRITICAL_GOVERNANCE_DOCS = [
    "docs/governance/AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md",
    "docs/governance/GOVERNANCE_DOCUMENTS_MANIFEST.md",
    "docs/governance/AUTONOMOUS_MERGE_SAFETY_CHECKLIST.md",
]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_governance_control_plane_files_exist():
    assert README.exists(), "README.md must exist"
    assert INDEX.exists(), "AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md must exist"
    assert MANIFEST.exists(), "GOVERNANCE_DOCUMENTS_MANIFEST.md must exist"

    for rel in CRITICAL_GOVERNANCE_DOCS:
        path = REPO_ROOT / rel
        assert path.exists(), f"Critical governance document missing: {rel}"


def test_readme_links_to_governance_entrypoint():
    readme = _read_text(README)
    assert "docs/governance/AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md" in readme, (
        "README.md must link to the autonomous governance operations index"
    )


def test_index_declares_canonical_control_plane_and_links_manifest():
    index_text = _read_text(INDEX)
    assert "canonical" in index_text.lower(), (
        "Governance operations index must declare canonical control-plane intent"
    )
    assert "docs/governance/GOVERNANCE_DOCUMENTS_MANIFEST.md" in index_text, (
        "Governance operations index must link the governance documents manifest"
    )


def test_manifest_lists_critical_governance_documents():
    manifest_text = _read_text(MANIFEST)
    for rel in CRITICAL_GOVERNANCE_DOCS:
        assert rel in manifest_text, (
            f"Governance manifest must list critical governance document: {rel}"
        )


def test_index_links_all_critical_governance_documents_except_itself():
    index_text = _read_text(INDEX)
    for rel in CRITICAL_GOVERNANCE_DOCS:
        if rel == "docs/governance/AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md":
            continue
        assert rel in index_text, (
            f"Governance operations index must link critical governance document: {rel}"
        )
