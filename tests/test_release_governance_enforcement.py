from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.release_governance_check import REQUIRED_DOCS, validate_release_governance


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_release_governance_validation_passes() -> None:
    result = validate_release_governance()
    assert result["ok"], json.dumps(result, indent=2)


def test_release_governance_validator_reports_expected_files() -> None:
    result = validate_release_governance()
    checked = set(Path(p).name for p in result["checked_files"])
    expected = set(REQUIRED_DOCS.keys())
    assert checked == expected


def test_release_governance_cli_returns_json() -> None:
    completed = subprocess.run(
        [sys.executable, "tools/release_governance_check.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert "checked_files" in payload
    assert "errors" in payload
