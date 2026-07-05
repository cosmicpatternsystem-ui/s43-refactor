from pathlib import Path


def test_release_governance_workflow_exists():
    workflow = Path(".github/workflows/release-governance-gate.yml")
    assert workflow.exists(), "release governance workflow must exist"


def test_release_governance_workflow_has_expected_contract():
    workflow = Path(".github/workflows/release-governance-gate.yml")
    text = workflow.read_text(encoding="utf-8")

    required_fragments = [
        "name: Release Governance Gate",
        "pull_request:",
        "workflow_dispatch:",
        "python tools/release_governance_check.py",
        "python -m pytest tests/test_release_governance_enforcement.py -q",
        "actions/checkout@v4",
        "actions/setup-python@v5",
    ]

    for fragment in required_fragments:
        assert fragment in text, f"missing workflow fragment: {fragment}"