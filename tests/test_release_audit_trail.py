import json
import subprocess
import sys
from pathlib import Path

from tools.release_audit_trail_check import validate_audit_artifact


def test_audit_trail_policy_exists():
    path = Path("docs/release/audit-trail-policy.md")
    assert path.exists(), "audit trail policy must exist"

    text = path.read_text(encoding="utf-8")
    assert "Release Audit Trail Policy" in text
    assert "policy_audit_passed" in text
    assert "tools/release_audit_trail_check.py" in text


def test_sample_release_audit_is_valid():
    path = Path("docs/release/audit/sample-release-audit.json")
    errors = validate_audit_artifact(path)
    assert errors == []


def test_validator_cli_reports_success():
    result = subprocess.run(
        [sys.executable, "tools/release_audit_trail_check.py"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["errors"] == []
