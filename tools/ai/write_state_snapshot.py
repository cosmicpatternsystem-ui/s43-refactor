#!/usr/bin/env python3
"""Write a local Phase 22 repository state snapshot without reading file contents."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence


SNAPSHOT_PATH = Path("AI_AUDIT/current_state_snapshot.json")
ROADMAP_JSON = Path("AUDIT/ROADMAP_CURRENT.json")
DEFERRED_PATHS = [
    "AI_AUDIT/",
    "tools/ai/bridge_claude.py",
    "tools/ai/bridge_claude_repo.py",
    "tools/ai/s43_supervisor.py",
]


def run_git(args: Sequence[str], root: Path) -> Dict[str, object]:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "args": ["git", *args],
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def git_stdout(args: Sequence[str], root: Path) -> str:
    result = run_git(args, root)
    return str(result["stdout"])


def repo_root() -> Path:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        raise RuntimeError("not inside a Git repository")
    return Path(completed.stdout.strip()).resolve()


def load_roadmap(root: Path) -> Dict[str, object]:
    path = root / ROADMAP_JSON
    if not path.is_file():
        return {"error": f"missing {ROADMAP_JSON}"}
    return json.loads(path.read_text(encoding="utf-8"))


def build_snapshot(root: Path) -> Dict[str, object]:
    upstream = git_stdout(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], root)
    ahead_behind = ""
    if upstream:
        ahead_behind = git_stdout(["rev-list", "--left-right", "--count", f"HEAD...{upstream}"], root)

    status_lines = git_stdout(["status", "--short", "--branch"], root).splitlines()
    return {
        "schema_version": 1,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repo": str(root),
        "branch": git_stdout(["branch", "--show-current"], root),
        "commit": git_stdout(["rev-parse", "--short", "HEAD"], root),
        "upstream": upstream,
        "ahead_behind": ahead_behind,
        "status_short_branch": status_lines,
        "deferred_paths": DEFERRED_PATHS,
        "roadmap": load_roadmap(root),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write AI_AUDIT/current_state_snapshot.json.")
    parser.add_argument("--repo", default=".", help="Repository path; default is current directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.repo).resolve()
    if args.repo == ".":
        root = repo_root()
    snapshot = build_snapshot(root)
    path = root / SNAPSHOT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WROTE: {SNAPSHOT_PATH}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
