import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "artifact-retention-scheduled-audit.yml"
AUDIT_PATH = ROOT / "docs" / "security" / "audit" / "artifact-retention-scheduled-audit.json"


def read_workflow():
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def test_artifact_retention_scheduled_audit_workflow_exists():
    assert WORKFLOW_PATH.exists()


def test_artifact_retention_scheduled_audit_has_schedule_and_dispatch():
    workflow = read_workflow()
    assert "on:" in workflow
    assert "schedule:" in workflow
    assert '- cron: "17 3 * * 1"' in workflow
    assert "workflow_dispatch:" in workflow


def test_artifact_retention_scheduled_audit_uses_pinned_actions_and_python():
    workflow = read_workflow()
    assert "actions/checkout@v4" in workflow
    assert "actions/setup-python@v5" in workflow
    assert 'python-version: "3.11"' in workflow


def test_artifact_retention_scheduled_audit_has_read_only_permissions_and_timeout():
    workflow = read_workflow()
    assert "permissions:" in workflow
    assert "contents: read" in workflow
    assert "timeout-minutes: 10" in workflow


def test_artifact_retention_scheduled_audit_installs_pytest_before_tests():
    workflow = read_workflow()
    assert "Install test dependencies" in workflow
    assert "python -m pip install --upgrade pip" in workflow
    assert "python -m pip install pytest" in workflow
    assert workflow.index("Install test dependencies") < workflow.index("Run artifact retention tests")


def test_artifact_retention_scheduled_audit_runs_compile_tests_and_validator():
    workflow = read_workflow()
    assert "python -m py_compile tools/artifact_retention_check.py" in workflow
    assert "python -m py_compile tests/test_artifact_retention_scheduled_audit.py" in workflow
    assert "python -m pytest tests/test_artifact_retention.py tests/test_artifact_retention_negative.py tests/test_artifact_retention_ci_gate.py tests/test_artifact_retention_scheduled_audit.py -q" in workflow
    assert "python tools/artifact_retention_check.py" in workflow


def test_artifact_retention_scheduled_audit_json_exists_and_is_valid():
    assert AUDIT_PATH.exists()
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    assert audit["schema_version"] == "aso-x.audit_artifact_retention_scheduled_audit.v1"
    assert audit["baseline"] == "P2.11"
    assert audit["name"] == "Artifact Retention Scheduled Audit"
    assert audit["status"] == "implemented"
    assert audit["source_baseline"] == "P2.10"
    assert audit["source_pr"] == 217
    assert audit["source_merge_commit"] == "6f03a96b0b607c165f44d907becafaa9911e2fdc"
    assert audit["workflow"] == ".github/workflows/artifact-retention-scheduled-audit.yml"
    assert audit["validator"] == "tools/artifact_retention_check.py"


def test_artifact_retention_scheduled_audit_json_controls_are_complete():
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    control_ids = {control["id"] for control in audit["controls"]}
    assert control_ids == {
        "P2.11-SCHED-001",
        "P2.11-SCHED-002",
        "P2.11-SCHED-003",
        "P2.11-SCHED-004",
    }
    assert all(control["status"] == "implemented" for control in audit["controls"])


def test_artifact_retention_scheduled_audit_files_are_lf_only_and_bom_free():
    for path in (WORKFLOW_PATH, AUDIT_PATH):
        content = path.read_bytes()
        assert b"\r" not in content
        assert not content.startswith(b"\xef\xbb\xbf")
