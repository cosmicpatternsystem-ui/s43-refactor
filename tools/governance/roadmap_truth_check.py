#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    ROOT / "docs/governance/REPOSITORY_TRUTH.md",
    ROOT / "docs/ai/AI_HANDOFF.md",
    ROOT / "docs/governance/GOAL_CONSTITUTION.md",
    ROOT / "docs/governance/ROADMAP_CONSTITUTION.md",
    ROOT / "ROADMAP_CURRENT.json",
    ROOT / "ROADMAP_CANONICAL.md",
    ROOT / "PROJECT_STATE.md",
    ROOT / "POLICY_MATRIX.md",
    ROOT / "ROADMAP.md",
]

NON_AUTHORITATIVE_PATTERNS = [
    r".*\.bak$",
    r".*\.tmp$",
    r".*\.old$",
    r".*\.orig$",
    r".*\.rej$",
    r".*\.RETIRED\.txt$",
    r".*\.disabled$",
    r".*patch_log.*$",
]


def fail(msg: str) -> None:
    sys.stdout.write(f"FAIL: {msg}\n")


def ok(msg: str) -> None:
    sys.stdout.write(f"OK: {msg}\n")


def read_text(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"BOM not allowed: {path.relative_to(ROOT)}")
    return data.decode("utf-8")


def assert_lf_only(path: Path) -> None:
    raw = path.read_bytes()
    if b"\r\n" in raw or b"\r" in raw.replace(b"\r\n", b""):
        raise ValueError(f"CRLF/CR not allowed: {path.relative_to(ROOT)}")


def main() -> int:
    rc = 0

    for f in REQUIRED_FILES:
        if not f.exists():
            fail(f"missing required file: {f.relative_to(ROOT)}")
            rc = 1
            continue

        try:
            read_text(f)
            assert_lf_only(f)
            ok(f"validated text encoding and line endings: {f.relative_to(ROOT)}")
        except Exception as e:
            fail(str(e))
            rc = 1

    if rc:
        return rc

    try:
        roadmap_json = json.loads(read_text(ROOT / "ROADMAP_CURRENT.json"))
    except Exception as e:
        fail(f"invalid ROADMAP_CURRENT.json: {e}")
        return 1

    if roadmap_json.get("canonical_roadmap") != "ROADMAP_CANONICAL.md":
        fail("ROADMAP_CURRENT.json canonical_roadmap must equal ROADMAP_CANONICAL.md")
        rc = 1
    else:
        ok("ROADMAP_CURRENT.json canonical_roadmap aligned")

    repo_truth = read_text(ROOT / "docs/governance/REPOSITORY_TRUTH.md")
    if "ROADMAP_CURRENT.json is the machine-readable active roadmap state." not in repo_truth:
        fail("repository truth missing machine-readable roadmap declaration")
        rc = 1
    else:
        ok("repository truth declares machine-readable roadmap state")

    if "ROADMAP_CANONICAL.md is the human-readable canonical roadmap." not in repo_truth:
        fail("repository truth missing canonical roadmap declaration")
        rc = 1
    else:
        ok("repository truth declares canonical roadmap")

    roadmap_constitution = read_text(ROOT / "docs/governance/ROADMAP_CONSTITUTION.md")
    if "ROADMAP_CURRENT.json is the active machine-readable roadmap state" not in roadmap_constitution:
        fail("roadmap constitution missing machine-readable rule")
        rc = 1
    else:
        ok("roadmap constitution declares machine-readable rule")

    if "ROADMAP_CANONICAL.md is the human-readable canonical roadmap" not in roadmap_constitution:
        fail("roadmap constitution missing canonical roadmap rule")
        rc = 1
    else:
        ok("roadmap constitution declares canonical roadmap rule")

    ai_handoff = read_text(ROOT / "docs/ai/AI_HANDOFF.md")
    for token in [
        "docs/governance/REPOSITORY_TRUTH.md",
        "PROJECT_STATE.md",
        "docs/governance/GOAL_CONSTITUTION.md",
        "docs/governance/ROADMAP_CONSTITUTION.md",
        "ROADMAP_CURRENT.json",
        "ROADMAP_CANONICAL.md",
        "POLICY_MATRIX.md",
    ]:
        if token not in ai_handoff:
            fail(f"AI handoff missing mandatory read token: {token}")
            rc = 1

    if rc == 0:
        ok("AI handoff mandatory read order present")

    canonical_md = read_text(ROOT / "ROADMAP_CANONICAL.md")
    if "human-readable canonical roadmap" not in canonical_md.lower():
        fail("ROADMAP_CANONICAL.md missing canonical identity declaration")
        rc = 1
    else:
        ok("ROADMAP_CANONICAL.md identity declaration present")

    derived_md = read_text(ROOT / "ROADMAP.md")
    if "non-prevailing" not in derived_md.lower():
        fail("ROADMAP.md must declare itself derivative and non-prevailing")
        rc = 1
    else:
        ok("ROADMAP.md derivative declaration present")

    bad_files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        rel = path.relative_to(ROOT).as_posix()
        for pattern in NON_AUTHORITATIVE_PATTERNS:
            if re.fullmatch(pattern, rel):
                bad_files.append(rel)
                break

    if bad_files:
        ok("non-authoritative retention artifacts detected")
        for rel in bad_files:
            sys.stdout.write(f"INFO: retention artifact: {rel}\n")
    else:
        ok("no retention artifacts detected")

    canonical_count = sum(
        1 for p in [ROOT / "ROADMAP_CANONICAL.md", ROOT / "CANONICAL_ROADMAP.md"]
        if p.exists()
    )
    if canonical_count > 1:
        fail("multiple canonical roadmap filenames detected")
        rc = 1
    else:
        ok("single canonical roadmap filename enforced")

    state_text = read_text(ROOT / "PROJECT_STATE.md")
    if "Governance State" not in state_text:
        fail("PROJECT_STATE.md missing Governance State section")
        rc = 1
    else:
        ok("PROJECT_STATE.md governance section present")

    policy_text = read_text(ROOT / "POLICY_MATRIX.md")
    for required_policy in [
        "repository_truth_enforced",
        "ai_handoff_enforced",
        "roadmap_truth_consistency",
        "backup_non_authoritative",
    ]:
        if required_policy not in policy_text:
            fail(f"POLICY_MATRIX.md missing required policy: {required_policy}")
            rc = 1

    if rc == 0:
        ok("POLICY_MATRIX.md required policies present")

    return rc


if __name__ == "__main__":
    raise SystemExit(main())