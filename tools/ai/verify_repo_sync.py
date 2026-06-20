#!/usr/bin/env python3
"""Non-destructive repository sync verifier for Phase 21."""

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


@dataclass
class CheckResult:
    level: str
    message: str


@dataclass
class GitCommandResult:
    returncode: int
    stdout: str
    stderr: str


def run_git(args: Sequence[str], repo: Optional[Path] = None) -> GitCommandResult:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(repo) if repo else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return GitCommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def add(results: List[CheckResult], level: str, message: str) -> None:
    results.append(CheckResult(level=level, message=message))


def first_line(value: str) -> str:
    return value.splitlines()[0].strip() if value.splitlines() else ""


def parse_ahead_behind(value: str) -> Tuple[Optional[int], Optional[int]]:
    parts = value.split()
    if len(parts) != 2:
        return None, None
    try:
        left = int(parts[0])
        right = int(parts[1])
    except ValueError:
        return None, None
    return left, right


def remote_ref_from_upstream(upstream: str) -> Optional[str]:
    if not upstream:
        return None
    if upstream.startswith("refs/remotes/"):
        return upstream
    return "refs/remotes/" + upstream


def is_dirty_status(status_output: str) -> bool:
    return bool(status_output.strip())


def inspect_repo(args: argparse.Namespace) -> Tuple[List[CheckResult], int]:
    results: List[CheckResult] = []

    root_result = run_git(["rev-parse", "--show-toplevel"])
    if root_result.returncode != 0 or not root_result.stdout:
        add(results, "FAIL", "not inside a Git work tree")
        return results, 1

    repo = Path(root_result.stdout).resolve()
    add(results, "INFO", f"repository: {repo}")

    inside_result = run_git(["rev-parse", "--is-inside-work-tree"], repo)
    if inside_result.returncode == 0 and inside_result.stdout == "true":
        add(results, "PASS", "inside Git work tree")
    else:
        add(results, "FAIL", "unable to confirm Git work tree")
        return results, 1

    branch_result = run_git(["branch", "--show-current"], repo)
    branch = first_line(branch_result.stdout)
    if branch_result.returncode != 0 or not branch:
        add(results, "FAIL", "current branch is detached or unknown")
    else:
        add(results, "PASS", f"current branch: {branch}")
        if args.expected_branch and branch != args.expected_branch:
            add(results, "FAIL", f"expected branch {args.expected_branch}, found {branch}")

    head_result = run_git(["rev-parse", "--short", "HEAD"], repo)
    if head_result.returncode == 0 and head_result.stdout:
        add(results, "INFO", f"current commit: {first_line(head_result.stdout)}")
    else:
        add(results, "FAIL", "unable to read current commit")

    upstream_result = run_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], repo)
    upstream = first_line(upstream_result.stdout)
    if upstream_result.returncode != 0 or not upstream:
        add(results, "FAIL", "missing configured upstream")
        upstream = ""
    else:
        add(results, "PASS", f"configured upstream: {upstream}")

    status_result = run_git(["status", "--short"], repo)
    if status_result.returncode != 0:
        add(results, "FAIL", "unable to read working tree status")
    elif is_dirty_status(status_result.stdout):
        if args.allow_dirty:
            add(results, "WARN", "working tree is dirty but allowed for documented dry-run condition")
        else:
            add(results, "FAIL", "working tree is dirty")
        for line in status_result.stdout.splitlines():
            add(results, "INFO", f"status: {line}")
    else:
        add(results, "PASS", "working tree is clean")

    if upstream:
        remote_ref = remote_ref_from_upstream(upstream)
        if remote_ref:
            remote_show = run_git(["show-ref", "--verify", remote_ref], repo)
            if remote_show.returncode == 0:
                add(results, "PASS", f"remote tracking ref present: {remote_ref}")
            else:
                add(results, "FAIL", f"remote tracking ref missing: {remote_ref}")

            remote_meta = run_git(
                [
                    "for-each-ref",
                    "--format=%(refname:short) %(objectname:short) %(committerdate:iso8601)",
                    remote_ref,
                ],
                repo,
            )
            if remote_meta.returncode == 0 and remote_meta.stdout:
                add(results, "INFO", f"remote fetch state: {remote_meta.stdout}")
            else:
                add(results, "FAIL", "unable to inspect remote fetch state")

        counts_result = run_git(["rev-list", "--left-right", "--count", "HEAD...@{upstream}"], repo)
        ahead, behind = parse_ahead_behind(counts_result.stdout)
        if counts_result.returncode != 0 or ahead is None or behind is None:
            add(results, "FAIL", "unable to calculate ahead/behind counts")
        else:
            add(results, "INFO", f"ahead: {ahead}")
            add(results, "INFO", f"behind: {behind}")
            if ahead > 0 and behind > 0:
                add(results, "FAIL", "branch is divergent from upstream")
            elif behind > 0:
                add(results, "FAIL", "branch is behind upstream")
            elif ahead > 0:
                if args.allow_ahead:
                    add(results, "WARN", "branch is ahead of upstream but allowed for documented dry-run condition")
                else:
                    add(results, "FAIL", "branch is ahead of upstream")
            else:
                add(results, "PASS", "branch is synchronized with upstream")

    failure_count = sum(1 for item in results if item.level == "FAIL")
    warning_count = sum(1 for item in results if item.level == "WARN")

    if failure_count:
        add(results, "FAIL", f"sync verification failed with {failure_count} blocking issue(s)")
        return results, 1

    if warning_count:
        add(results, "PASS", f"sync verification passed with {warning_count} documented dry-run warning(s)")
        return results, 0

    add(results, "PASS", "sync verification passed")
    return results, 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Non-destructive Git branch, upstream, working tree, and divergence verifier."
    )
    parser.add_argument(
        "--expected-branch",
        default="main",
        help="Expected current branch. Use an empty value to skip branch-name enforcement.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow a dirty working tree only as a documented local dry-run condition.",
    )
    parser.add_argument(
        "--allow-ahead",
        action="store_true",
        help="Allow ahead-of-upstream state only as a documented local dry-run condition.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.expected_branch == "":
        args.expected_branch = None

    results, exit_code = inspect_repo(args)
    print("Phase 21 repository sync verification")
    print("Mode: non-destructive read-only inspection")
    if args.allow_dirty or args.allow_ahead:
        allowed = []
        if args.allow_dirty:
            allowed.append("dirty")
        if args.allow_ahead:
            allowed.append("ahead")
        print("Allowed dry-run condition(s): " + ", ".join(allowed))
    else:
        print("Allowed dry-run condition(s): none")
    print("")

    for item in results:
        print(f"{item.level}: {item.message}")

    print("")
    print("RESULT: " + ("PASS" if exit_code == 0 else "FAIL"))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
