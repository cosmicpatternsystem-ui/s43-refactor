import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "docs" / "roadmap" / "roadmap.index.json"
REQ_ID_RE = re.compile(r"^ASO-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}$")

def assert_utf8_no_bom_lf(path):
    data = path.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in data
    assert b"\r" not in data
    data.decode("utf-8")

def test_roadmap_index_exists_and_is_valid_json():
    assert INDEX_PATH.exists()
    assert_utf8_no_bom_lf(INDEX_PATH)
    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    assert payload["canonical_source"] == "docs/ROADMAP.md"
    assert payload["horizon_years"] >= 50
    assert payload["status"] == "active"

def test_governance_documents_exist():
    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    docs = payload.get("governance_documents", [])
    assert docs
    for rel in docs:
        path = ROOT / rel
        assert path.exists()
        assert_utf8_no_bom_lf(path)

def test_requirement_ids_are_unique_and_valid():
    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    ids = [r["id"] for r in payload["requirements"]]
    assert len(ids) == len(set(ids))
    for rid in ids:
        assert REQ_ID_RE.match(rid)
