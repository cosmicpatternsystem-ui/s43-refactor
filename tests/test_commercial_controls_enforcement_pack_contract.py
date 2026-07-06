from pathlib import Path


DOC = Path("docs/strategy/COMMERCIAL_CONTROLS_ENFORCEMENT_PACK.md")


def test_commercial_controls_enforcement_pack_exists():
    assert DOC.exists(), f"Missing document: {DOC}"


def test_commercial_controls_enforcement_pack_markers():
    text = DOC.read_text(encoding="utf-8")

    required_markers = [
        "# Commercial Controls Enforcement Pack",
        "Status: Canonical",
        "Type: Normative",
        "Governance: Repository-governed",
        "Enforcement: Commercially binding",
        "## Purpose",
        "## Scope",
        "## Enforcement Principles",
        "## Required Evidence",
        "## Hard Stop Conditions",
        "## Exception Workflow",
        "## Approval Integrity",
        "## Cash and Margin Protection",
        "## Delivery Truth Controls",
        "## Counterparty Fitness Controls",
        "## Auditability and Retention",
        "## Enforcement Posture",
        "## Minimum Review Triggers",
        "## Renewal and Revalidation",
        "## Repository Control Standard",
        "## Enforcement",
    ]

    for marker in required_markers:
        assert marker in text, f"Missing marker: {marker}"


def test_commercial_controls_enforcement_pack_hard_controls():
    text = DOC.read_text(encoding="utf-8")

    required_controls = [
        "undocumented discount",
        "margin below approved floor",
        "unapproved payment extension",
        "missing approver authority",
        "Undocumented = invalid.",
        "Unapproved = non-binding.",
        "Unverifiable = rejected.",
        "Commercially unsafe = blocked.",
        "No commercial exception is valid if it is not documented.",
        "No side agreement outside repository-governed controls is recognized as valid internally.",
        "cash certainty outranks booked optimism",
        "revenue quality outranks headline revenue",
        "margin discipline outranks discretionary discounting",
        "Delivery truth outranks sales enthusiasm.",
        "Historical precedent alone is not approval.",
    ]

    for control in required_controls:
        assert control in text, f"Missing control: {control}"
