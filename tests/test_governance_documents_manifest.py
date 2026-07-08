from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "governance" / "GOVERNANCE_DOCUMENTS_MANIFEST.md"
INDEX = ROOT / "docs" / "governance" / "AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md"
README = ROOT / "README.md"


CRITICAL_ARTIFACTS = [
    "README.md",
    "docs/governance/AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md",
    "docs/governance/AUTONOMOUS_FAILURE_HANDLING_RUNBOOK.md",
    "docs/governance/AUTONOMOUS_RECOVERY_AND_ROLLBACK_RUNBOOK.md",
    "docs/governance/AUTONOMOUS_MERGE_SAFETY_CHECKLIST.md",
]

INDEX_LINK_TARGETS = [
    "docs/governance/AUTONOMOUS_FAILURE_HANDLING_RUNBOOK.md",
    "docs/governance/AUTONOMOUS_RECOVERY_AND_ROLLBACK_RUNBOOK.md",
    "docs/governance/AUTONOMOUS_MERGE_SAFETY_CHECKLIST.md",
    "docs/governance/GOVERNANCE_DOCUMENTS_MANIFEST.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_governance_documents_manifest_exists():
    assert MANIFEST.exists(), "governance documents manifest must exist"


def test_governance_documents_manifest_lists_critical_artifacts():
    text = _read(MANIFEST)
    for artifact in CRITICAL_ARTIFACTS:
        assert artifact in text


def test_manifest_critical_artifacts_exist():
    for artifact in CRITICAL_ARTIFACTS:
        assert (ROOT / artifact).exists(), f"{artifact} must exist"


def test_autonomous_governance_index_links_manifest():
    text = _read(INDEX)
    assert "docs/governance/GOVERNANCE_DOCUMENTS_MANIFEST.md" in text


def test_readme_links_autonomous_governance_index():
    text = _read(README)
    assert "docs/governance/AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md" in text


def test_index_links_required_governance_targets():
    text = _read(INDEX)
    for artifact in INDEX_LINK_TARGETS:
        assert artifact in text