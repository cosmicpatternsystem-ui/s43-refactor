#!/usr/bin/env python3
"""Fail-closed guard for the Phase 22 living roadmap."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


ROADMAP_MD = Path("AUDIT/ROADMAP_CURRENT.md")
ROADMAP_JSON = Path("AUDIT/ROADMAP_CURRENT.json")
REQUIRED_JSON_FIELDS = {
    "schema_version",
    "roadmap_version",
    "source_of_truth",
    "current_phase",
    "current_focus",
    "status",
    "required_artifacts",
    "blocked_actions",
    "deferred_paths",
}


class GuardFailure(Exception):
    pass


def load_roadmap(root: Path) -> Dict[str, Any]:
    md_path = root / ROADMAP_MD
    json_path = root / ROADMAP_JSON

    if not md_path.is_file():
        raise GuardFailure(f"missing roadmap markdown: {ROADMAP_MD}")
    if not json_path.is_file():
        raise GuardFailure(f"missing roadmap json: {ROADMAP_JSON}")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GuardFailure(f"invalid roadmap json: {exc}") from exc

    if not isinstance(data, dict):
        raise GuardFailure("roadmap json must be an object")

    missing = sorted(REQUIRED_JSON_FIELDS - set(data))
    if missing:
        raise GuardFailure("roadmap json missing required fields: " + ", ".join(missing))

    if data.get("source_of_truth") != "repository_files_only":
        raise GuardFailure("roadmap source_of_truth must be repository_files_only")

    required_artifacts = data.get("required_artifacts")
    if not isinstance(required_artifacts, list) or not required_artifacts:
        raise GuardFailure("required_artifacts must be a non-empty list")

    missing_artifacts: List[str] = []
    for item in required_artifacts:
        if not isinstance(item, str):
            raise GuardFailure("required_artifacts entries must be strings")
        if not (root / item).exists():
            missing_artifacts.append(item)

    if missing_artifacts:
        raise GuardFailure("missing required artifacts: " + ", ".join(missing_artifacts))

    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify Phase 22 living roadmap files exist and are valid.")
    parser.add_argument("--repo", default=".", help="Repository root path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.repo).resolve()
    try:
        data = load_roadmap(root)
    except GuardFailure as exc:
        print(f"FAIL: {exc}")
        return 1

    print("PASS: living roadmap files are present and valid")
    print(f"phase: {data['current_phase']}")
    print(f"focus: {data['current_focus']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
