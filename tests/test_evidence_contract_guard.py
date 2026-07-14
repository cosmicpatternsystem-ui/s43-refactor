from pathlib import Path

LEGACY_TERMS = ("evidence_type", "content_hash")
SCAN_ROOTS = (
    Path("src"),
    Path("scripts"),
    Path("tests"),
    Path("artifacts/evidence"),
    Path("asoctl.py"),
)
EXCLUDED_PATHS = {
    Path("tests/test_evidence_contract_guard.py"),
}
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
}

INCLUDED_SUFFIXES = {
    ".py",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".ps1",
    ".psm1",
    ".psd1",
}


def _iter_scan_files(repo_root: Path):
    for root in SCAN_ROOTS:
        target = repo_root / root
        if not target.exists():
            continue

        if target.is_file():
            rel = target.relative_to(repo_root)
            if rel not in EXCLUDED_PATHS and rel.suffix.lower() in INCLUDED_SUFFIXES:
                yield target, rel
            continue

        for path in target.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(repo_root)
            if rel in EXCLUDED_PATHS:
                continue
            if set(rel.parts) & EXCLUDED_PARTS:
                continue
            if rel.suffix.lower() not in INCLUDED_SUFFIXES:
                continue
            yield path, rel


def _read_text_with_fallbacks(path: Path) -> str | None:
    for encoding in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return None


def test_no_live_legacy_evidence_contract_terms():
    repo_root = Path(__file__).resolve().parents[1]
    hits = []
    unreadable = []

    for path, rel in _iter_scan_files(repo_root):
        text = _read_text_with_fallbacks(path)
        if text is None:
            unreadable.append(str(rel))
            continue

        for term in LEGACY_TERMS:
            if term in text:
                hits.append(f"{rel}: {term}")

    assert not unreadable, "Unreadable files in contract guard scope:\n" + "\n".join(sorted(unreadable))
    assert not hits, "Legacy Evidence contract terms found:\n" + "\n".join(sorted(hits))