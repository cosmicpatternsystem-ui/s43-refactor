#!/usr/bin/env python3
"""Phase 21 command safety policy for local AI supervision."""

from __future__ import annotations

import argparse
import shlex
from dataclasses import dataclass
from typing import Iterable, Sequence, Tuple


ALLOWED_READ_ONLY_COMMANDS: Tuple[Tuple[str, ...], ...] = (
    ("pwd",),
    ("git", "status"),
    ("git", "branch", "--show-current"),
    ("git", "rev-parse"),
    ("git", "rev-list"),
    ("git", "for-each-ref"),
    ("git", "show-ref"),
    ("git", "ls-files"),
    ("git", "log"),
    ("git", "remote", "-v"),
    ("find",),
    ("sort",),
    ("python3", "-B", "tools/ai/verify_repo_sync.py"),
    ("python3", "-B", "tools/ai/precommit_inventory.py"),
    ("python3", "-B", "tools/ai/run_supervised_phase21_cycle.py"),
)

BLOCKED_COMMANDS: Tuple[Tuple[str, ...], ...] = (
    ("git", "add"),
    ("git", "commit"),
    ("git", "push"),
    ("git", "reset"),
    ("git", "checkout"),
    ("git", "clean"),
    ("git", "switch"),
    ("git", "tag"),
    ("rmdir",),
    ("unlink",),
    ("shred",),
)

APPROVAL_REQUIRED_COMMANDS: Tuple[Tuple[str, ...], ...] = (
    ("rm", "-rf", "tools/ai/__pycache__"),
    ("rm",),
    ("git", "fetch"),
    ("git", "pull"),
    ("git", "merge"),
    ("git", "rebase"),
    ("git", "branch"),
    ("gh",),
    ("curl",),
    ("wget",),
    ("npm", "publish"),
    ("python3", "-B", "-m", "py_compile"),
    ("python3",),
)


@dataclass(frozen=True)
class PolicyDecision:
    status: str
    reason: str


def starts_with(tokens: Sequence[str], prefix: Sequence[str]) -> bool:
    return len(tokens) >= len(prefix) and tuple(tokens[: len(prefix)]) == tuple(prefix)


def matches_any(tokens: Sequence[str], prefixes: Iterable[Sequence[str]]) -> bool:
    return any(starts_with(tokens, prefix) for prefix in prefixes)


def classify_command(command: str) -> PolicyDecision:
    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        return PolicyDecision("blocked", f"unable to parse command: {exc}")

    if not tokens:
        return PolicyDecision("blocked", "empty command")

    if matches_any(tokens, BLOCKED_COMMANDS):
        return PolicyDecision("blocked", "command is destructive or repository-mutating")

    if matches_any(tokens, ALLOWED_READ_ONLY_COMMANDS):
        return PolicyDecision("allowed", "command matches read-only Phase 21 policy")

    if matches_any(tokens, APPROVAL_REQUIRED_COMMANDS):
        return PolicyDecision("approval-required", "command may mutate state, access network, or run broad interpreter logic")

    return PolicyDecision("approval-required", "command is not in the explicit read-only allowlist")


def print_policy() -> None:
    print("Phase 21 safety policy")
    print("Allowed read-only command prefixes:")
    for item in ALLOWED_READ_ONLY_COMMANDS:
        print("  " + " ".join(item))
    print("Blocked command prefixes:")
    for item in BLOCKED_COMMANDS:
        print("  " + " ".join(item))
    print("Approval-required command prefixes:")
    for item in APPROVAL_REQUIRED_COMMANDS:
        print("  " + " ".join(item))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify commands against the Phase 21 safety policy.")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to classify. If omitted, print policy.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.command:
        print_policy()
        return 0

    command_parts = args.command
    if command_parts and command_parts[0] == "--":
        command_parts = command_parts[1:]
    command = " ".join(command_parts)
    decision = classify_command(command)
    print(f"{decision.status.upper()}: {command}")
    print(f"Reason: {decision.reason}")
    return 0 if decision.status == "allowed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
