#!/usr/bin/env python3
"""Append timestamped Phase 22 roadmap event JSON files."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Sequence


EVENT_DIR = Path("AI_AUDIT/roadmap_events")


def run_git(args: Sequence[str], root: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


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


def safe_slug(value: str) -> str:
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    slug = "".join(ch if ch in allowed else "_" for ch in value).strip("_")
    return slug[:80] or "event"


def build_event(root: Path, event_type: str, summary: str) -> Dict[str, object]:
    return {
        "schema_version": 1,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "event_type": event_type,
        "summary": summary,
        "repo": str(root),
        "branch": run_git(["branch", "--show-current"], root),
        "commit": run_git(["rev-parse", "--short", "HEAD"], root),
        "status_short_branch": run_git(["status", "--short", "--branch"], root).splitlines(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append a timestamped roadmap event JSON file.")
    parser.add_argument("--repo", default=".", help="Repository path; default is current repository.")
    parser.add_argument("--event-type", required=True, help="Short event type, for example validation_passed.")
    parser.add_argument("--summary", required=True, help="Human-readable event summary. Do not include secrets.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.repo).resolve()
    if args.repo == ".":
        root = repo_root()

    event = build_event(root, args.event_type, args.summary)
    event_dir = root / EVENT_DIR
    event_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S_%f_UTC")
    path = event_dir / f"{stamp}_{safe_slug(args.event_type)}.json"
    path.write_text(json.dumps(event, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WROTE: {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
