#!/usr/bin/env python3
"""Fail if deferred AI artifacts or tools are tracked in Git."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, Sequence


FORBIDDEN_TRACKED_PATHS = (
    "AI_AUDIT/",
    "tools/ai/bridge_claude.py",
    "tools/ai/bridge_claude_repo.py",
    "tools/ai/s43_supervisor.py",
)


def run_git(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def tracked_files() -> List[str]:
    result = run_git(["ls-files"])
    if result.returncode != 0:
        message = result.stderr.strip() or "git ls-files failed"
        raise RuntimeError(message)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_forbidden(path: str) -> bool:
    normalized = Path(path).as_posix()
    for forbidden in FORBIDDEN_TRACKED_PATHS:
        if forbidden.endswith("/"):
            if normalized.startswith(forbidden):
                return True
        elif normalized == forbidden:
            return True
    return False


def main() -> int:
    try:
        tracked = tracked_files()
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    violations = sorted(path for path in tracked if is_forbidden(path))
    if violations:
        print("FAIL: forbidden deferred AI artifacts are tracked:")
        for path in violations:
            print(f"- {path}")
        print("Deferred AI artifacts must remain untracked or be replaced by sanitized AUDIT summaries.")
        return 1

    print("PASS: no forbidden deferred AI artifacts are tracked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
