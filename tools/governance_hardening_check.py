from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    "PROJECT_CHARTER.md",
    "repo/contracts/CANONICAL_SOURCES.yaml",
    "docs/ROADMAP.md",
    "docs/governance/GOVERNANCE_BASELINE.md",
    "docs/governance/LOCK_SCHEMA.json",
    "docs/governance/LOCK_REGISTRY.json",
    "docs/governance/POLICY_MATRIX.md",
    "docs/governance/DECISION_LOG.md",
    "docs/governance/COMPATIBILITY_CONTRACT.md",
    "docs/OPERATIONS_RUNBOOK.md",
    "docs/COMMERCIAL_MODEL.md",
    ".github/workflows/governance-enforcement.yml",
    ".github/workflows/release-governance-gate.yml",
    ".github/workflows/artifact-retention-gate.yml",
]

REQUIRED_FRAGMENTS = {
    "PROJECT_CHARTER.md": [
        "The repository must function as the source of truth",
        "50-Year Thesis",
        "Continuity Rule",
    ],
    "repo/contracts/CANONICAL_SOURCES.yaml": [
        "canonical_sources:",
        "chat_memory_is_not_source_of_truth: true",
        "canonical_paths_must_exist: true",
    ],
    "docs/governance/POLICY_MATRIX.md": [
        "Change Type",
        "Required Evidence",
        "Blocking Conditions",
    ],
    "docs/governance/DECISION_LOG.md": [
        "Append-only governance ledger",
        "DECISION-20260706-001",
    ],
    "docs/governance/COMPATIBILITY_CONTRACT.md": [
        "BOM-free UTF-8",
        "LF",
        "Python 3.11",
    ],
    "docs/OPERATIONS_RUNBOOK.md": [
        "Clean Sync Procedure",
        "CI Failure Triage",
        "Disaster Recovery",
    ],
    "docs/COMMERCIAL_MODEL.md": [
        "Commercial Thesis",
        "Customer Profiles",
        "Monetization Options",
    ],
}


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise AssertionError(f"file has UTF-8 BOM: {path}")
    if b"\r\n" in raw:
        raise AssertionError(f"file has CRLF line endings: {path}")
    return raw.decode("utf-8")


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing required governance file: {rel}")
            continue
        if path.is_file():
            try:
                read_text(path)
            except Exception as exc:
                errors.append(str(exc))

    for rel, fragments in REQUIRED_FRAGMENTS.items():
        path = ROOT / rel
        if not path.exists():
            continue
        try:
            text = read_text(path)
        except Exception:
            continue
        for fragment in fragments:
            if fragment not in text:
                errors.append(f"missing fragment in {rel}: {fragment}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("OK: governance hardening pack validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())