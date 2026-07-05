from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.sbom_check import DEFAULT_ARTIFACT, validate_sbom_artifact


REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "docs/security/sbom-policy.md"
ARTIFACT_PATH = REPO_ROOT / DEFAULT_ARTIFACT


def test_sbom_policy_exists() -> None:
    assert POLICY_PATH.exists()
    text = POLICY_PATH.read_text(encoding="utf-8")
    assert "P2.7 SBOM Baseline Policy" in text
    assert "aso-x.sbom." in text
    assert "network-free" in text


def test_sample_sbom_artifact_is_valid() -> None:
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert validate_sbom_artifact(data) == []


def test_sample_sbom_artifact_links_to_p2_5_and_p2_6() -> None:
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    assert (
        data["release_evidence_bundle_path"]
        == "docs/release/audit/sample-release-evidence-bundle.json"
    )
    assert (
        data["supply_chain_integrity_path"]
        == "docs/security/audit/sample-supply-chain-integrity.json"
    )


def test_sample_sbom_components_are_non_empty() -> None:
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    components = data["components"]
    assert components
    assert any(component["type"] == "lockfile" for component in components)
    assert any(component["type"] == "manifest" for component in components)
    assert any(
        component["name"] == "supply-chain-integrity-baseline"
        for component in components
    )


def test_sbom_cli_default_artifact_passes() -> None:
    completed = subprocess.run(
        [sys.executable, "tools/sbom_check.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr

    result = json.loads(completed.stdout)
    assert result["ok"] is True
    assert result["errors"] == []


def test_sbom_cli_explicit_artifact_passes() -> None:
    completed = subprocess.run(
        [sys.executable, "tools/sbom_check.py", str(DEFAULT_ARTIFACT)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr

    result = json.loads(completed.stdout)
    assert result["ok"] is True
    assert result["artifact"] == str(DEFAULT_ARTIFACT)