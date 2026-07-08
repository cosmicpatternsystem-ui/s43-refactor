from pathlib import Path

RELEASE_DOCS = {
    "release-governance.md": [
        "release",
        "audit",
        "safe merge",
        "rollback",
        "dependency",
        "artifact",
    ],
    "versioning-policy.md": [
        "version",
        "rollback",
        "audit",
        "release",
    ],
    "rollback-protocol.md": [
        "rollback",
        "incident",
        "artifact",
        "audit",
    ],
    "incident-response-protocol.md": [
        "incident",
        "severity",
        "rollback",
        "audit",
    ],
    "production-readiness-checklist.md": [
        "readiness",
        "rollback",
        "dependency",
        "artifact",
        "audit",
    ],
    "dependency-freeze-policy.md": [
        "dependency",
        "freeze",
        "rollback",
        "audit",
    ],
    "artifact-integrity-policy.md": [
        "artifact",
        "integrity",
        "checksum",
        "audit",
    ],
}


def test_release_governance_docs_exist_and_are_readable():
    base = Path("docs/release")
    assert base.is_dir(), "docs/release directory is required"

    for filename in RELEASE_DOCS:
        path = base / filename
        assert path.is_file(), f"missing release governance doc: {path}"
        text = path.read_text(encoding="utf-8")
        assert text.startswith("# P2.0 "), f"{path} must start with a P2.0 heading"
        assert "\r\n" not in text, f"{path} must use LF line endings"


def test_release_governance_docs_contain_required_terms():
    base = Path("docs/release")

    for filename, terms in RELEASE_DOCS.items():
        text = (base / filename).read_text(encoding="utf-8").lower()
        for term in terms:
            assert term in text, f"{filename} must mention required term: {term}"
