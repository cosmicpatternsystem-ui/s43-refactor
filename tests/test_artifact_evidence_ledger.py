from pathlib import Path

from tools.artifact_evidence_ledger_check import validate_ledger_record


def test_artifact_evidence_ledger_record_is_valid() -> None:
    data = validate_ledger_record()
    assert data["record_type"] == "artifact_retention_evidence_ledger"
    assert data["durability_target"] == "50y"
    assert data["result"] == "pass"


def test_artifact_evidence_ledger_record_references_repo_files() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    data = validate_ledger_record()

    referenced = []
    referenced.append(Path(data["policy"]["path"]))
    referenced.extend(Path(p) for p in data["evidence_inputs"])
    referenced.extend(Path(p) for p in data["validators"])
    referenced.extend(Path(p) for p in data["tests"])

    for rel in referenced:
        assert (repo_root / rel).exists(), f"Missing referenced file: {rel}"