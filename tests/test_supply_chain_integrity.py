from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.supply_chain_integrity_check import validate_supply_chain_integrity

POLICY_PATH = Path("docs/security/supply-chain-integrity-policy.md")
ARTIFACT_PATH = Path("docs/security/audit/sample-supply-chain-integrity.json")


def test_policy_file_exists() -> None:
    assert POLICY_PATH.exists(), f"missing policy file: {POLICY_PATH}"


def test_sample_supply_chain_integrity_artifact_is_valid() -> None:
    errors = validate_supply_chain_integrity(ARTIFACT_PATH)
    assert errors == []


def test_sample_supply_chain_integrity_json_loads() -> None:
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == "aso-x.supply_chain_integrity.v1"
    assert data["network_free_validation"] is True
    assert data["mutable_external_sources_allowed"] is False
    assert data["policy_audit_passed"] is True


def test_cli_validator_succeeds() -> None:
    result = subprocess.run(
        [sys.executable, "tools/supply_chain_integrity_check.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True