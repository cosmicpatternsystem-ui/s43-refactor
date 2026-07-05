from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "artifact-retention-gate.yml"
AUDIT_PATH = REPO_ROOT / "docs" / "security" / "audit" / "artifact-retention-ci-gate.json"


def test_artifact_retention_gate_workflow_exists():
    assert WORKFLOW_PATH.exists()


def test_artifact_retention_gate_runs_on_prs_and_main_pushes():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "pull_request:" in content
    assert "push:" in content
    assert "branches:" in content
    assert "- main" in content


def test_artifact_retention_gate_uses_pinned_major_actions():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "actions/checkout@v4" in content
    assert "actions/setup-python@v5" in content


def test_artifact_retention_gate_uses_python_311():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert 'python-version: "3.11"' in content


def test_artifact_retention_gate_compile_checks_validator_and_tests():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "python -m py_compile" in content
    assert "tools/artifact_retention_check.py" in content
    assert "tests/test_artifact_retention.py" in content
    assert "tests/test_artifact_retention_negative.py" in content


def test_artifact_retention_gate_runs_positive_and_negative_tests():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "python -m pytest" in content
    assert "tests/test_artifact_retention.py" in content
    assert "tests/test_artifact_retention_negative.py" in content
    assert "-q" in content


def test_artifact_retention_gate_runs_validator():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "python tools/artifact_retention_check.py" in content


def test_artifact_retention_gate_has_read_only_contents_permission():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "permissions:" in content
    assert "contents: read" in content


def test_artifact_retention_gate_has_timeout():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "timeout-minutes: 10" in content


def test_artifact_retention_ci_gate_audit_evidence_exists():
    assert AUDIT_PATH.exists()