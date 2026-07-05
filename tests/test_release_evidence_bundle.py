from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.release_evidence_bundle_check import validate_release_evidence_bundle

POLICY_PATH = Path("docs/release/release-evidence-bundle-policy.md")
ARTIFACT_PATH = Path("docs/release/audit/sample-release-evidence-bundle.json")


def test_policy_file_exists() -> None:
    assert POLICY_PATH.exists(), f"missing policy file: {POLICY_PATH}"


def test_sample_release_evidence_bundle_is_valid() -> None:
    errors = validate_release_evidence_bundle(ARTIFACT_PATH)
    assert errors == []


def test_sample_release_evidence_bundle_json_loads() -> None:
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == "aso-x.release_evidence_bundle.v1"
    assert data["policy_audit_passed"] is True


def test_cli_validator_succeeds() -> None:
    result = subprocess.run(
        [sys.executable, "tools/release_evidence_bundle_check.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True