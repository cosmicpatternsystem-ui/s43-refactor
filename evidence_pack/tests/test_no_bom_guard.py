from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".json", ".md", ".py", ".yml", ".yaml", ".txt"}

BOMS = {
    b"\xef\xbb\xbf": "UTF-8 BOM",
    b"\xff\xfe": "UTF-16 LE BOM",
    b"\xfe\xff": "UTF-16 BE BOM",
}


def iter_text_files():
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def test_evidence_pack_text_files_do_not_start_with_bom():
    offenders = []

    for path in iter_text_files():
        data = path.read_bytes()

        for bom, label in BOMS.items():
            if data.startswith(bom):
                offenders.append(f"{path.relative_to(ROOT)} starts with {label}")

        text = data[:16].decode("utf-8", errors="ignore")
        if text.startswith("\ufeff"):
            offenders.append(f"{path.relative_to(ROOT)} starts with decoded U+FEFF")
        if text.startswith("ï¿"):
            offenders.append(f"{path.relative_to(ROOT)} starts with mojibake BOM marker")

    assert not offenders, "BOM markers found:\n" + "\n".join(offenders)