from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs" / "governance" / "global-governance-locks.json"
SCHEMA_PATH = ROOT / "docs" / "governance" / "global-governance-locks.schema.json"
INDEX_PATH = ROOT / "docs" / "governance" / "GLOBAL_GOVERNANCE_LOCKS.md"


def load_json(path: Path) -> dict:
return json.loads(path.read_text(encoding="utf-8"))


def test_global_governance_files_exist() -> None:
assert REGISTRY_PATH.exists()
assert SCHEMA_PATH.exists()
assert INDEX_PATH.exists()


def test_registry_shape_and_minimum_lock_count() -> None:
registry = load_json(REGISTRY_PATH)
assert registry["system"] == "global-governance-lock-system"
assert registry["status"] == "active"
assert registry["target_durability"] == "50y"
assert registry["source_of_truth"] == "repository"
assert registry["minimum_lock_count"] >= 32
assert registry["failure_mode"] == "block merge"
assert len(registry["locks"]) >= registry["minimum_lock_count"]


def test_lock_ids_are_unique_and_canonical() -> None:
registry = load_json(REGISTRY_PATH)
ids = [lock["id"] for lock in registry["locks"]]
assert len(ids) == len(set(ids))
for lock_id in ids:
assert re.fullmatch(r"GOV-LOCK-[0-9]{3}", lock_id), lock_id


def test_active_locks_have_required_governance_fields() -> None:
registry = load_json(REGISTRY_PATH)
required = {
"id",
"name",
"status",
"scope",
"owner",
"risk_class",
"retention",
"enforcement",
"change_control",
"failure_mode",
"evidence_required",
"supersession_allowed",
"deletion_allowed",
"immutable",
"source_of_truth",
}

for lock in registry["locks"]:
assert required.issubset(lock), lock.get("id")
assert lock["status"] in {"active", "superseded", "retired"}
assert lock["risk_class"] in {"critical", "high", "medium", "low"}
assert lock["retention"] == "50y"
assert lock["failure_mode"] == "block merge"
assert lock["source_of_truth"] == "repo"
assert lock["deletion_allowed"] is False
assert lock["owner"]
assert lock["scope"]
assert lock["change_control"]


def test_enforcement_is_not_documentation_only() -> None:
registry = load_json(REGISTRY_PATH)
required = {
"documentation",
"json-registry",
"schema-validation",
"pytest",
"github-actions",
}

for lock in registry["locks"]:
assert required.issubset(set(lock["enforcement"])), lock["id"]


def test_critical_and_high_locks_require_evidence() -> None:
registry = load_json(REGISTRY_PATH)
for lock in registry["locks"]:
if lock["risk_class"] in {"critical", "high"}:
assert lock["evidence_required"] is True, lock["id"]


def test_immutable_locks_are_not_deletable() -> None:
registry = load_json(REGISTRY_PATH)
immutable = [lock for lock in registry["locks"] if lock["immutable"]]
assert immutable

for lock in immutable:
assert lock["deletion_allowed"] is False
assert lock["supersession_allowed"] is True


def test_markdown_index_mentions_every_lock() -> None:
registry = load_json(REGISTRY_PATH)
index = INDEX_PATH.read_text(encoding="utf-8")
for lock in registry["locks"]:
assert lock["id"] in index
assert lock["name"] in index


def test_schema_contains_required_global_constraints() -> None:
schema = load_json(SCHEMA_PATH)
assert schema["properties"]["system"]["const"] == "global-governance-lock-system"
assert schema["properties"]["target_durability"]["const"] == "50y"
assert schema["properties"]["failure_mode"]["const"] == "block merge"
assert schema["properties"]["locks"]["minItems"] >= 32


def test_governance_files_are_utf8_lf_and_bom_free() -> None:
paths = [
REGISTRY_PATH,
SCHEMA_PATH,
INDEX_PATH,
ROOT / "docs" / "governance" / "GOVERNANCE_CHANGE_CONTROL.md",
ROOT / "docs" / "governance" / "EVIDENCE_LEDGER_POLICY.md",
ROOT / "docs" / "governance" / "ARTIFACT_RETENTION_POLICY.md",
]

for path in paths:
data = path.read_bytes()
assert not data.startswith(b"\xef\xbb\xbf"), str(path)
assert b"\r\n" not in data, str(path)