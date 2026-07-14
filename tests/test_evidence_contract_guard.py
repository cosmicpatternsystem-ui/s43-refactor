from pathlib import Path

LEGACY_TERMS = ("evidence_type", "content_hash")
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
}
EXCLUDED_PREFIXES = (
    Path("artifacts/audits"),
)

INCLUDED_SUFFIXES = {
    ".py",
    ".json",
    ".md",
    ".yml",
    ".yaml",
    ".toml",
    ".txt",
    ".ps1",
    ".psm1",
    ".psd1",
}


def _is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDED_PARTS:
        return True
    return any(path == prefix or prefix in path.parents for prefix in EXCLUDED_PREFIXES)


def _should_scan(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in INCLUDED_SUFFIXES and not _is_excluded(path)


def test_no_live_legacy_evidence_contract_terms():
    repo_root = Path(__file__).resolve().parents[1]
    hits = []

    for path in repo_root.rglob("*"):
        rel = path.relative_to(repo_root)
        if not _should_scan(rel):
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8-sig")

        for term in LEGACY_TERMS:
            if term in text:
                hits.append(f"{rel}: {term}")

    assert not hits, "Legacy Evidence contract terms found:\n" + "\n".join(sorted(hits))