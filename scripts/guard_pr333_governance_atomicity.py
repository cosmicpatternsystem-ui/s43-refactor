#!/usr/bin/env python
from __future__ import annotations

import subprocess
import sys

MD = "docs/governance/ROADMAP_CANONICAL.md"
JSON = "docs/governance/ROADMAP_CURRENT.json"

def run_git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "git {} failed with exit code {}\nstdout:\n{}\nstderr:\n{}".format(
                " ".join(args), proc.returncode, proc.stdout, proc.stderr
            )
        )
    return proc.stdout

def changed_in_head() -> set[str]:
    out = run_git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD")
    return {line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()}

def changed_in_worktree_and_index() -> set[str]:
    names: set[str] = set()
    for args in (
        ("diff", "--name-only", "--", MD, JSON),
        ("diff", "--cached", "--name-only", "--", MD, JSON),
    ):
        out = run_git(*args)
        for line in out.splitlines():
            line = line.strip().replace("\\", "/")
            if line:
                names.add(line)
    return names

def assert_atomic(label: str, changed: set[str]) -> bool:
    md = MD in changed
    js = JSON in changed
    print(f"{label}: MD={md} JSON={js}")
    if md != js:
        print(
            f"FAIL: governance atomicity violated in {label}: {MD} and {JSON} must change together",
            file=sys.stderr,
        )
        return False
    return True

def main() -> int:
    ok = True
    ok = assert_atomic("HEAD diff-tree", changed_in_head()) and ok
    ok = assert_atomic("working-tree/index diff", changed_in_worktree_and_index()) and ok
    if not ok:
        print("\\nRemediation: update both governance artifacts together", file=sys.stderr)
        return 1
    print("PASS: PR333 governance atomicity guard")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
