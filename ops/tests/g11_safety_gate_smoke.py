#!/usr/bin/env python3
"""Standalone smoke test for the G11 safety-gate invariant.

This test reads s43.py as plain text. It does not import or execute runtime code.
"""

from pathlib import Path
import re
import sys


ENABLED_RE = re.compile(
    r"^\s*self\._g11_safety_gates_enabled\s*=\s*True\s*(#.*)?$"
)
DISABLED_RE = re.compile(
    r"^\s*self\._g11_safety_gates_enabled\s*=\s*False\s*(#.*)?$"
)


def active_assignment_matches(lines, pattern):
    matches = []

    for line_number, line in enumerate(lines, start=1):
        stripped = line.lstrip()

        if not stripped:
            continue

        if stripped.startswith("#"):
            continue

        if pattern.match(line):
            matches.append((line_number, line.rstrip()))

    return matches


def print_matches(label, matches):
    print(f"{label}: {len(matches)}")

    for line_number, line in matches:
        print(f"  line {line_number}: {line}")


def main():
    repo_root = Path(__file__).resolve().parents[2]
    s43_path = repo_root / "s43.py"

    if not s43_path.is_file():
        print(f"FAIL: s43.py not found at {s43_path}")
        return 1

    lines = s43_path.read_text(encoding="utf-8").splitlines()

    enabled_matches = active_assignment_matches(lines, ENABLED_RE)
    disabled_matches = active_assignment_matches(lines, DISABLED_RE)

    if len(enabled_matches) == 1 and len(disabled_matches) == 0:
        line_number, _line = enabled_matches[0]
        print(
            "OK: G11 safety gates are enabled with exactly one active "
            f"assignment at line {line_number}"
        )
        return 0

    print("FAIL: unexpected G11 safety-gate assignment state")
    print_matches("active enabled assignments", enabled_matches)
    print_matches("active disabled assignments", disabled_matches)
    return 1


if __name__ == "__main__":
    sys.exit(main())
