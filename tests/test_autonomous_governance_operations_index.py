from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "governance" / "AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md"

REQUIRED_CONTROL_DOCUMENTS = [
    "docs/governance/AUTONOMOUS_FAILURE_HANDLING_RUNBOOK.md",
    "docs/governance/AUTONOMOUS_RECOVERY_AND_ROLLBACK_RUNBOOK.md",
    "docs/governance/AUTONOMOUS_MERGE_SAFETY_CHECKLIST.md",
]

REQUIRED_SECTIONS = [
    "# Autonomous Governance Operations Index",
    "## Purpose",
    "## Operating Model",
    "## Primary Documents",
    "## Decision Routing",
    "## Standard Operating Sequence",
    "## Failure Routing",
    "## Recovery Routing",
    "## Merge Routing",
    "## Evidence Routing",
    "## Stop Conditions",
    "## Maintenance Rules",
]


def test_autonomous_governance_operations_index_exists():
    assert INDEX.exists(), "autonomous governance operations index must exist"
    assert INDEX.is_file(), "autonomous governance operations index must be a file"


def test_autonomous_governance_operations_index_routes_primary_documents():
    text = INDEX.read_text(encoding="utf-8")

    for document in REQUIRED_CONTROL_DOCUMENTS:
        assert document in text, f"missing governance routing reference: {document}"


def test_autonomous_governance_operations_index_keeps_required_operational_sections():
    text = INDEX.read_text(encoding="utf-8")

    for section in REQUIRED_SECTIONS:
        assert section in text, f"missing required operations index section: {section}"


def test_autonomous_governance_operations_index_defines_stop_and_evidence_controls():
    text = INDEX.read_text(encoding="utf-8").lower()

    required_terms = [
        "minimum evidence",
        "branch name",
        "base commit",
        "changed files",
        "validation commands",
        "validation results",
        "pull request number",
        "merge commit",
        "stop and do not continue",
        "local and remote repository state disagree",
        "validation results are missing or contradictory",
        "rewrite published history",
    ]

    for term in required_terms:
        assert term in text, f"missing required evidence or stop-control term: {term}"