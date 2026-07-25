from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROADMAP_ID_PATTERN = re.compile(r"\bP\d-[A-Z0-9-]+\b")

REQUIRED_FILES = [
    "AGENT_ENTRYPOINT.md",
    "PROJECT_CHARTER.md",
    "docs/COMMERCIAL_MODEL.md",
    "docs/OPERATIONS_RUNBOOK.md",
    "docs/governance/GOAL_CONSTITUTION.md",
    "docs/governance/SOURCE_OF_TRUTH_HIERARCHY.md",
    "docs/governance/WORK_PROTOCOL.md",
    "docs/governance/AUTONOMY_MODEL.md",
    "docs/governance/DURABILITY_STANDARD.md",
    "docs/governance/POLICY_MATRIX.md",
    "docs/governance/COMPATIBILITY_CONTRACT.md",
    "docs/governance/DECISION_LOG.md",
    "docs/governance/ROADMAP_CURRENT.json",
    "docs/governance/ROADMAP_CANONICAL.md",
    "repo/contracts/CANONICAL_SOURCES.yaml",
    "repo/contracts/PROJECT_CONSTITUTION.yaml",
    "tests/test_project_constitution_pack.py",
    ".github/workflows/project-constitution-gate.yml",
]

REQUIRED_PHRASES = {
    "AGENT_ENTRYPOINT.md": [
        "repository evidence",
        "mandatory read order",
        "chat memory",
        "system of record",
    ],
    "docs/governance/GOAL_CONSTITUTION.md": [
        "50-year",
        "commercial",
        "global",
        "non-negotiable",
        "success criteria",
    ],
    "docs/governance/SOURCE_OF_TRUTH_HIERARCHY.md": [
        "precedence",
        "conflict",
        "repository",
        "roadmap",
        "safety",
    ],
    "docs/governance/WORK_PROTOCOL.md": [
        "validation",
        "pull request",
        "merge",
        "failure",
    ],
    "docs/governance/AUTONOMY_MODEL.md": [
        "level 0",
        "level 5",
        "level 3",
        "level 4",
    ],
    "docs/governance/DURABILITY_STANDARD.md": [
        "utf-8",
        "bom-free",
        "lf",
        "anti-obsolescence",
        "artifact retention",
    ],
    "docs/governance/ROADMAP_CANONICAL.md": [
        "P0-ROADMAP-AUTHORITY",
        "P0-PHASE-02-COMMERCIAL-VALIDATION",
        "canonical machine-readable roadmap authority",
    ],
    "repo/contracts/PROJECT_CONSTITUTION.yaml": [
        "repository_is_source_of_truth: true",
        "chat_memory_is_source_of_truth: false",
        "commercial_posture:",
        "autonomy_targets:",
        "canonical_files:",
    ],
}


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def read_text(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        fail(f"{path.as_posix()} contains UTF-8 BOM")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"{path.as_posix()} is not valid UTF-8: {exc}")
    if "\r" in text:
        fail(f"{path.as_posix()} must use LF line endings only")
    if not text.endswith("\n"):
        fail(f"{path.as_posix()} must end with a final newline")
    return text


def ensure_required_files() -> dict[str, str]:
    texts: dict[str, str] = {}
    for rel in REQUIRED_FILES:
        path = ROOT / rel
        if not path.exists():
            fail(f"missing required file: {rel}")
        texts[rel] = read_text(path)
    return texts


def ensure_required_phrases(texts: dict[str, str]) -> None:
    for rel, phrases in REQUIRED_PHRASES.items():
        text = texts[rel].lower()
        for phrase in phrases:
            if phrase.lower() not in text:
                fail(f"{rel} missing required phrase: {phrase}")


def extract_roadmap_ids(value: object) -> list[str]:
    ids: list[str] = []

    def collect(candidate: object) -> None:
        if isinstance(candidate, str) and ROADMAP_ID_PATTERN.fullmatch(candidate):
            ids.append(candidate)

    def visit(node: object) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                collect(key)
                visit(child)
            return
        if isinstance(node, list):
            for child in node:
                visit(child)
            return
        collect(node)

    visit(value)

    unique_ids: list[str] = []
    for item in ids:
        if item not in unique_ids:
            unique_ids.append(item)
    return unique_ids


def roadmap_ids_from_json(text: str) -> list[str]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        fail(f"docs/governance/ROADMAP_CURRENT.json is invalid JSON: {exc}")

    ids = extract_roadmap_ids(data)
    if not ids:
        fail("docs/governance/ROADMAP_CURRENT.json does not expose any roadmap ids")
    return ids


def roadmap_ids_from_markdown(text: str) -> list[str]:
    ids = ROADMAP_ID_PATTERN.findall(text)
    unique_ids: list[str] = []
    for item in ids:
        if item not in unique_ids:
            unique_ids.append(item)
    return unique_ids


def ensure_roadmap_sync(texts: dict[str, str]) -> None:
    json_ids = roadmap_ids_from_json(texts["docs/governance/ROADMAP_CURRENT.json"])
    md_ids = roadmap_ids_from_markdown(texts["docs/governance/ROADMAP_CANONICAL.md"])

    missing_ids = [item for item in md_ids if item not in json_ids]
    if missing_ids:
        fail(
            "canonical roadmap ids missing from docs/governance/ROADMAP_CURRENT.json: "
            f"{missing_ids}"
        )


def ensure_constitution_links(texts: dict[str, str]) -> None:
    charter = texts["PROJECT_CHARTER.md"]
    expected_refs = [
        "AGENT_ENTRYPOINT.md",
        "docs/governance/GOAL_CONSTITUTION.md",
        "docs/governance/SOURCE_OF_TRUTH_HIERARCHY.md",
        "docs/governance/WORK_PROTOCOL.md",
        "docs/governance/AUTONOMY_MODEL.md",
        "docs/governance/DURABILITY_STANDARD.md",
        "repo/contracts/CANONICAL_SOURCES.yaml",
        "repo/contracts/PROJECT_CONSTITUTION.yaml",
        "docs/governance/ROADMAP_CURRENT.json",
        "docs/governance/ROADMAP_CANONICAL.md",
    ]
    for ref in expected_refs:
        if ref not in charter:
            fail(f"project charter does not reference {ref}")


def main() -> int:
    texts = ensure_required_files()
    ensure_required_phrases(texts)
    ensure_roadmap_sync(texts)
    ensure_constitution_links(texts)
    print("OK: project constitution and autonomous governance layer validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
