#!/usr/bin/env python3
"""Non-destructive precommit inventory for Phase 21 review."""

from __future__ import annotations

import argparse
import fnmatch
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


SUSPICIOUS_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}

SUSPICIOUS_PATTERNS = (
    "*.log",
    "*.tmp",
    "*.bak",
    "*.swp",
    "*.swo",
    "*.pyc",
    "*.pyo",
    "*.key",
    "*.pem",
    "*.p12",
    "*.pfx",
    "*token*",
    "*secret*",
    "*credential*",
    "*credentials*",
    "*private*key*",
)

IGNORED_DIR_NAMES = {".git"}
DEFAULT_LARGE_FILE_BYTES = 1_000_000
EXPECTED_PHASE21_PREFIXES = (
    "AUDIT/PHASE21_",
    "AI_AUDIT/",
    "tools/ai/",
)


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    reason: str


def run_git(args: Sequence[str], repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def repo_root() -> Path:
    result = run_git(["rev-parse", "--show-toplevel"], Path.cwd())
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError("not inside a Git repository")
    return Path(result.stdout.strip()).resolve()


def git_status_paths(repo: Path) -> List[str]:
    result = run_git(["status", "--porcelain=v1"], repo)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "unable to read git status")

    paths: List[str] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        raw = line[3:].strip()
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        if raw:
            paths.append(raw)
    return sorted(set(paths))


def iter_repo_files(repo: Path) -> Iterable[Path]:
    for root, dirs, files in os.walk(repo):
        root_path = Path(root)
        dirs[:] = [item for item in dirs if item not in IGNORED_DIR_NAMES]
        for name in files:
            yield root_path / name


def is_expected_phase21_path(rel: str) -> bool:
    return rel.startswith(EXPECTED_PHASE21_PREFIXES)


def suspicious_reason(path: Path, rel: str, large_file_bytes: int) -> List[str]:
    reasons: List[str] = []
    name_lower = path.name.lower()
    rel_lower = rel.lower()

    if path.name == "__pycache__" or "__pycache__" in path.parts:
        reasons.append("python cache path")

    if name_lower in SUSPICIOUS_NAMES:
        reasons.append("suspicious secret or environment filename")

    for pattern in SUSPICIOUS_PATTERNS:
        if fnmatch.fnmatch(name_lower, pattern.lower()) or fnmatch.fnmatch(rel_lower, pattern.lower()):
            reasons.append(f"matches pattern {pattern}")

    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    if size > large_file_bytes:
        reasons.append(f"large file {size} bytes")

    return sorted(set(reasons))


def collect_findings(repo: Path, large_file_bytes: int, scan_all: bool) -> List[Finding]:
    findings: List[Finding] = []

    dirty_paths = git_status_paths(repo)
    for rel in dirty_paths:
        if not is_expected_phase21_path(rel):
            findings.append(Finding("WARN", rel, "dirty path outside expected Phase 21 scope"))

    if scan_all:
        candidate_paths = iter_repo_files(repo)
    else:
        candidate_paths = ((repo / rel) for rel in dirty_paths)

    for path in candidate_paths:
        rel = path.relative_to(repo).as_posix()
        if not path.exists():
            continue
        if path.is_dir():
            if path.name == "__pycache__":
                findings.append(Finding("FAIL", rel, "python cache path"))
            continue
        reasons = suspicious_reason(path, rel, large_file_bytes)
        for reason in reasons:
            severity = "FAIL"
            if reason.startswith("large file") and is_expected_phase21_path(rel):
                severity = "WARN"
            findings.append(Finding(severity, rel, reason))

    return sorted(set(findings), key=lambda item: (item.severity, item.path, item.reason))


def print_inventory(repo: Path, findings: List[Finding], dirty_paths: List[str]) -> None:
    print("Phase 21 precommit inventory")
    print(f"Repository: {repo}")
    print("")
    print("Dirty paths:")
    if dirty_paths:
        for path in dirty_paths:
            print(f"  {path}")
    else:
        print("  none")
    print("")
    print("Suspicious findings:")
    if findings:
        for finding in findings:
            print(f"{finding.severity}: {finding.path}: {finding.reason}")
    else:
        print("PASS: no suspicious files found")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report suspicious files before Phase 21 human commit review.")
    parser.add_argument("--large-file-bytes", type=int, default=DEFAULT_LARGE_FILE_BYTES)
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Return success while still printing findings. Use only for local dry-run review.",
    )
    parser.add_argument(
        "--scan-all",
        action="store_true",
        help="Scan the full repository instead of only current dirty paths.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo = repo_root()
        dirty_paths = git_status_paths(repo)
        findings = collect_findings(repo, args.large_file_bytes, args.scan_all)
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print_inventory(repo, findings, dirty_paths)
    failures = [item for item in findings if item.severity == "FAIL"]
    if failures and not args.warn_only:
        print("")
        print(f"RESULT: FAIL ({len(failures)} blocking suspicious finding(s))")
        return 1

    if findings:
        print("")
        print(f"RESULT: PASS WITH WARNINGS ({len(findings)} finding(s) documented)")
        return 0

    print("")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
