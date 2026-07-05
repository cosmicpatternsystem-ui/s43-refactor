from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.provenance_attestation_check import validate_artifact

ARTIFACT_PATH = Path("docs/security/audit/sample-provenance-attestation.json")
POLICY_PATH = Path("docs/security/provenance-attestation-policy.md")


def test_policy_file_exists() -> None:
    assert POLICY_PATH.exists()


def test_artifact_json_loads() -> None:
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_sample_artifact_is_valid() -> None:
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert validate_artifact(data) == []


def test_cross_links_present() -> None:
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert data["release_evidence_bundle_path"] == "docs/release/audit/sample-release-evidence-bundle.json"
    assert data["supply_chain_integrity_path"] == "docs/security/audit/sample-supply-chain-integrity.json"
    assert data["sbom_path"] == "docs/security/audit/sample-sbom.json"


def test_subject_and_materials_present() -> None:
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert data["subject"]["name"] == "sample-sbom"
    assert len(data["predicate"]["materials"]) >= 3


def test_cli_validator_default_artifact() -> None:
    result = subprocess.run(
        [sys.executable, "tools/provenance_attestation_check.py"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_cli_validator_explicit_artifact() -> None:
    result = subprocess.run(
        [sys.executable, "tools/provenance_attestation_check.py", str(ARTIFACT_PATH)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr