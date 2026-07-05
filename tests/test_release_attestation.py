from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.release_attestation_check import validate_attestation_artifact


POLICY_PATH = Path("docs/release/release-attestation-policy.md")
SAMPLE_ARTIFACT = Path("docs/release/audit/sample-release-attestation.json")


def test_release_attestation_policy_exists() -> None:
    assert POLICY_PATH.exists()
    text = POLICY_PATH.read_text(encoding="utf-8")
    assert "# Release Attestation Policy" in text
    assert "aso-x.release_attestation." in text


def test_sample_release_attestation_is_valid() -> None:
    assert validate_attestation_artifact(SAMPLE_ARTIFACT) == []


def test_validator_cli_reports_success() -> None:
    result = subprocess.run(
        [sys.executable, "tools/release_attestation_check.py"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    report = json.loads(result.stdout)
    assert report["ok"] is True
    assert report["artifact"] == "docs/release/audit/sample-release-attestation.json"
    assert report["errors"] == []
