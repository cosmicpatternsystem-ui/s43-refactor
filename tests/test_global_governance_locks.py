import json
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "governance" / "global-locks" / "registry.json"
SCHEMA_PATH = ROOT / "governance" / "global-locks" / "registry.schema.json"
DOC_PATH = ROOT / "docs" / "governance" / "global-governance-locks.md"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "global-governance-locks.yml"

EXPECTED_IDS = [f"GOV-LOCK-{number:03d}" for number in range(1, 33)]


def read_text(path: pathlib.Path) -> str:
    data = path.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf"), f"{path} must be UTF-8 without BOM"
    text = data.decode("utf-8")
    assert "\r" not in text, f"{path} must use LF line endings"
    assert text.endswith("\n"), f"{path} must end with newline"
    return text


def test_registry_json_is_valid_and_complete() -> None:
    registry = json.loads(read_text(REGISTRY_PATH))
    assert registry["schema_version"] == "1.0.0"
    assert registry["system"] == "ASO-X Global Governance Lock System"
    assert registry["lock_count"] == 32
    locks = registry["locks"]
    assert len(locks) == 32
    ids = [lock["id"] for lock in locks]
    assert ids == EXPECTED_IDS
    assert len(set(ids)) == 32
    for lock in locks:
        assert re.fullmatch(r"GOV-LOCK-\d{3}", lock["id"])
        assert lock["title"]
        assert lock["status"] == "locked"
        assert lock["category"]
        assert lock["severity"] == "blocking"
        assert lock["owner"] == "global-governance"
        assert lock["rationale"]
        assert "tests/test_global_governance_locks.py" in lock["enforcement"]
        assert "governance/global-locks/registry.json" in lock["artifacts"]


def test_schema_json_is_valid_and_requires_full_registry() -> None:
    schema = json.loads(read_text(SCHEMA_PATH))
    assert schema["title"] == "ASO-X Global Governance Lock Registry"
    assert schema["type"] == "object"
    assert schema["properties"]["lock_count"]["const"] == 32
    assert schema["properties"]["locks"]["minItems"] == 32
    assert schema["properties"]["locks"]["maxItems"] == 32


def test_markdown_index_mentions_every_lock() -> None:
    text = read_text(DOC_PATH)
    assert "# Global Governance Lock System" in text
    for lock_id in EXPECTED_IDS:
        assert lock_id in text


def test_workflow_yaml_is_present_and_targets_this_gate() -> None:
    text = read_text(WORKFLOW_PATH)
    assert "name: Global Governance Locks" in text
    assert "python -m pytest tests/test_global_governance_locks.py" in text
    assert "pull_request:" in text


def test_no_legacy_broken_builder_is_tracked() -> None:
    broken_builder = ROOT / "build_global_governance_lock_system.py"
    assert not broken_builder.exists(), "Remove broken temporary builder script"
