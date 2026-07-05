from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.artifact_retention_check import validate_artifact


def test_policy_file_exists() -> None:
    assert Path("docs/security/artifact-retention-policy.md").is_file()


def test_sample_artifact_loads_as_json_object() -> None:
    artifact = json.loads(
        Path("docs/security/audit/sample-artifact-retention.json").read_text(encoding="utf-8")
    )
    assert isinstance(artifact, dict)


def test_sample_artifact_is_valid() -> None:
    artifact = json.loads(
        Path("docs/security/audit/sample-artifact-retention.json").read_text(encoding="utf-8")
    )
    assert validate_artifact(artifact) == []


def test_cross_links_present() -> None:
    artifact = json.loads(
        Path("docs/security/audit/sample-artifact-retention.json").read_text(encoding="utf-8")
    )
    assert artifact["release_evidence_bundle_path"].endswith(".json")
    assert artifact["supply_chain_integrity_path"].endswith(".json")
    assert artifact["sbom_path"].endswith(".json")
    assert artifact["provenance_attestation_path"].endswith(".json")


def test_artifact_inventory_non_empty() -> None:
    artifact = json.loads(
        Path("docs/security/audit/sample-artifact-retention.json").read_text(encoding="utf-8")
    )
    artifacts = artifact["artifacts"]
    assert artifacts
    assert any(item["category"] == "provenance" for item in artifacts)
    assert any(item["category"] == "sbom" for item in artifacts)
    assert any(item["category"] == "supply-chain" for item in artifacts)


def test_cli_validator_default_artifact_succeeds() -> None:
    completed = subprocess.run(
        [sys.executable, "tools/artifact_retention_check.py"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert '"ok": true' in completed.stdout