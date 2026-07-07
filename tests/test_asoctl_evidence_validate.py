from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_evidence_validate_command_passes_for_example_record() -> None:
    completed = subprocess.run(
        [sys.executable, "asoctl.py", "evidence", "validate"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["decision"] == "pass"
    assert payload["errors"] == []
    assert payload["evidence_path"] == "artifacts/examples/evidence_record.example.json"
    assert payload["schema_path"] == "repo/schemas/evidence_record.schema.json"