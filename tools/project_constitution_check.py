from __future__ import annotations

from pathlib import Path
import sys
import re


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "AGENT_ENTRYPOINT.md",
    "PROJECT_CHARTER.md",
    "docs/ROADMAP.md",
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
    "repo/contracts/CANONICAL_SOURCES.yaml",
    "repo/contracts/PROJECT_CONSTITUTION.yaml",
    "repo/roadmap/roadmap.yaml",
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
    "repo/contracts/PROJECT_CONSTITUTION.yaml": [
        "repository_is_source_of_truth: true",
        "chat_memory_is_source_of_truth: false",
        "commercial_posture:",
        "autonomy_targets:",
        "canonical_files:",
    ],
    "repo/roadmap/roadmap.yaml": [
        "roadmap_items:",
        "R-001",
        "R-008",
    ],
    "docs/ROADMAP.md": [
        "R-001",
        "R-008",
        "Canonical source",
    ],
}


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


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


def roadmap_ids_from_yaml(text: str) -> list[str]:
    return re.findall(r"^\s*-\s*id:\s*(R-\d{3})\s*$", text, flags=re.MULTILINE)


def roadmap_ids_from_markdown(text: str) -> list[str]:
    return re.findall(r"\b(R-\d{3})\b", text)


def ensure_roadmap_sync(texts: dict[str, str]) -> None:
    yaml_ids = roadmap_ids_from_yaml(texts["repo/roadmap/roadmap.yaml"])
    md_ids = roadmap_ids_from_markdown(texts["docs/ROADMAP.md"])
    md_unique = []
    for item in md_ids:
        if item not in md_unique:
            md_unique.append(item)
    if yaml_ids != md_unique:
        fail(
            "roadmap ids differ between repo/roadmap/roadmap.yaml and docs/ROADMAP.md: "
            f"{yaml_ids} != {md_unique}"
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
        "repo/roadmap/roadmap.yaml",
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
