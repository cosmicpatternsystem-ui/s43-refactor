from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CANONICAL_MACHINE = REPO_ROOT / "docs" / "governance" / "ROADMAP_CURRENT.json"
CANONICAL_HUMAN = REPO_ROOT / "docs" / "governance" / "ROADMAP_CANONICAL.md"

AUTHORITY_DOCS = [
    REPO_ROOT / "docs" / "governance" / "REPOSITORY_TRUTH.md",
    REPO_ROOT / "docs" / "governance" / "SOURCE_OF_TRUTH_HIERARCHY.md",
    REPO_ROOT / "docs" / "governance" / "CANONICAL_ROADMAP_DECLARATION.md",
]

DERIVED_TEXT = [
    REPO_ROOT / "ROADMAP.md",
    REPO_ROOT / "docs" / "ROADMAP.md",
    REPO_ROOT / "docs" / "roadmap" / "aso-x-integrated-mandatory-roadmap.md",
]

DERIVED_JSON_LIKE = [
    REPO_ROOT / "docs" / "roadmap" / "roadmap.index.json",
]

LEGACY = [
    REPO_ROOT / "ROADMAP" / "ROADMAP_STATE.json",
    REPO_ROOT / "repo" / "roadmap" / "roadmap.yaml",
]

DERIVED_HEADER = "> DERIVED VIEW - NOT AUTHORITATIVE"
HUMAN_METADATA_START = "<!-- ASOX:CANONICAL_HUMAN_METADATA:START -->"
HUMAN_METADATA_END = "<!-- ASOX:CANONICAL_HUMAN_METADATA:END -->"

FORBIDDEN_AUTHORITY_CLAIMS = {
    "docs/ROADMAP.md": [r"canonical", r"authoritative", r"source of truth"],
    "ROADMAP.md": [r"canonical", r"authoritative", r"source of truth"],
    "docs/roadmap/aso-x-integrated-mandatory-roadmap.md": [r"canonical", r"authoritative", r"source of truth"],
    "docs/roadmap/roadmap.index.json": [r"canonical", r"authoritative", r"source of truth"],
    "docs/governance/ROADMAP_STATE.json": [r"canonical", r"authoritative", r"source of truth"],
    "repo/roadmap/roadmap.yaml": [r"canonical", r"authoritative", r"source of truth"],
}

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def fail(errors: list[str]) -> int:
    report = {"ok": False, "errors": errors}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1

def ok(data: dict) -> int:
    print(json.dumps({"ok": True, **data}, indent=2, ensure_ascii=False))
    return 0

def main() -> int:
    errors: list[str] = []

    if not CANONICAL_MACHINE.exists():
        errors.append(f"missing canonical machine file: {CANONICAL_MACHINE.relative_to(REPO_ROOT)}")
    if not CANONICAL_HUMAN.exists():
        errors.append(f"missing canonical human file: {CANONICAL_HUMAN.relative_to(REPO_ROOT)}")
    if errors:
        return fail(errors)

    machine_sha = sha256_file(CANONICAL_MACHINE)
    human_text = read_text(CANONICAL_HUMAN)

    if HUMAN_METADATA_START not in human_text or HUMAN_METADATA_END not in human_text:
        errors.append("canonical human metadata block missing from ROADMAP_CANONICAL.md")
    else:
        if "Canonical machine source: `ROADMAP_CURRENT.json`" not in human_text:
            errors.append("canonical human metadata does not reference ROADMAP_CURRENT.json")
        if f"`$json_sha = {machine_sha}`" not in human_text:
            errors.append("canonical human metadata SHA256 does not match ROADMAP_CURRENT.json")

    for path in AUTHORITY_DOCS:
        if not path.exists():
            errors.append(f"missing authority doc: {path.relative_to(REPO_ROOT)}")
            continue
        text = read_text(path)
        if "ROADMAP_CURRENT.json" not in text:
            errors.append(f"authority doc missing ROADMAP_CURRENT.json reference: {path.relative_to(REPO_ROOT)}")
        if "ROADMAP_CANONICAL.md" not in text:
            errors.append(f"authority doc missing ROADMAP_CANONICAL.md reference: {path.relative_to(REPO_ROOT)}")

    for path in DERIVED_TEXT:
        if not path.exists():
            continue
        text = read_text(path)
        if not text.startswith(DERIVED_HEADER):
            errors.append(f"derived text file missing non-authoritative header: {path.relative_to(REPO_ROOT)}")

    canonical_word = re.compile(r"\b(canonical|authoritative|source of truth)\b", re.IGNORECASE)

    for relative_str, patterns in FORBIDDEN_AUTHORITY_CLAIMS.items():
        path = REPO_ROOT / relative_str
        if not path.exists():
            continue
        text = read_text(path)
        if "DERIVED VIEW - NOT AUTHORITATIVE" in text:
            continue
        for raw_pat in patterns:
            if re.search(raw_pat, text, re.IGNORECASE):
                # allow explicit negation language in markdown docs where we inserted the managed block
                negations = [
                    "not authoritative",
                    "non-canonical",
                    "legacy or migration artifacts",
                    "must not be consumed by active enforcement",
                    "explicitly non-canonical",
                ]
                lowered = text.lower()
                if not any(n in lowered for n in negations):
                    errors.append(f"forbidden authority claim remains in {relative_str}")

    if errors:
        return fail(errors)

    data = {
        "canonical_machine": str(CANONICAL_MACHINE.relative_to(REPO_ROOT)),
        "canonical_human": str(CANONICAL_HUMAN.relative_to(REPO_ROOT)),
        "canonical_machine_sha256": machine_sha,
        "derived_text": [str(p.relative_to(REPO_ROOT)) for p in DERIVED_TEXT if p.exists()],
        "derived_json_like": [str(p.relative_to(REPO_ROOT)) for p in DERIVED_JSON_LIKE if p.exists()],
        "legacy": [str(p.relative_to(REPO_ROOT)) for p in LEGACY if p.exists()],
    }
    return ok(data)

if __name__ == "__main__":
    raise SystemExit(main())