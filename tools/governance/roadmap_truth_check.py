#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    ROOT / "docs/governance/REPOSITORY_TRUTH.md",
    ROOT / "docs/governance/SOURCE_OF_TRUTH_HIERARCHY.md",
    ROOT / "docs/governance/CANONICAL_ROADMAP_DECLARATION.md",
    ROOT / "docs/ai/AI_HANDOFF.md",
    ROOT / "docs/governance/GOAL_CONSTITUTION.md",
    ROOT / "docs/governance/ROADMAP_CONSTITUTION.md",
    ROOT / "docs/governance/ROADMAP_CURRENT.json",
    ROOT / "docs/governance/ROADMAP_CANONICAL.md",
    ROOT / "PROJECT_STATE.md",
    ROOT / "POLICY_MATRIX.md",
    ROOT / "ROADMAP.md",
    ROOT / "docs/roadmap/roadmap.index.json",
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
        roadmap_json = json.loads(read_text(ROOT / "docs/governance/ROADMAP_CURRENT.json"))
    except Exception as e:
        fail(f"invalid docs/governance/ROADMAP_CURRENT.json: {e}")
        return 1

    if roadmap_json.get("canonical_roadmap") != "docs/governance/ROADMAP_CANONICAL.md":
        fail("docs/governance/ROADMAP_CURRENT.json canonical_roadmap must equal docs/governance/ROADMAP_CANONICAL.md")
        rc = 1
    else:
        ok("docs/governance/ROADMAP_CURRENT.json canonical_roadmap aligned")

    repo_truth = read_text(ROOT / "docs/governance/REPOSITORY_TRUTH.md")
    for phrase, label in [
        ("`ROADMAP_CURRENT.json` is the machine-readable active roadmap state.", "repository truth declares machine-readable roadmap state"),
        ("`ROADMAP_CANONICAL.md` is the human-readable canonical roadmap.", "repository truth declares canonical roadmap"),
        ("`ROADMAP.md` and `docs/ROADMAP.md` are derivative roadmap views and must never override canonical truth.", "repository truth declares derivative roadmap views"),
        ("`docs/roadmap/roadmap.index.json` is a non-prevailing traceability index.", "repository truth declares traceability index"),
    ]:
        if phrase not in repo_truth:
            fail(f"repository truth missing declaration: {phrase}")
            rc = 1
        else:
            ok(label)

    source_hierarchy = read_text(ROOT / "docs/governance/SOURCE_OF_TRUTH_HIERARCHY.md")
    for phrase, label in [
        ("`ROADMAP_CURRENT.json` is the active machine-readable roadmap state.", "source hierarchy declares active machine-readable state"),
        ("`ROADMAP_CANONICAL.md` is the canonical human-readable roadmap.", "source hierarchy declares canonical human-readable roadmap"),
        ("`ROADMAP.md`, `docs/ROADMAP.md`, and `docs/roadmap/roadmap.index.json` are derivative, index, or public-facing views.", "source hierarchy declares derivative roadmap artifacts"),
        ("`repo/roadmap/roadmap.yaml` and `ROADMAP/ROADMAP_STATE.json` are non-authoritative unless explicitly promoted by a future governance PR and reflected in this hierarchy.", "source hierarchy declares legacy roadmap artifacts non-authoritative"),
    ]:
        if phrase not in source_hierarchy:
            fail(f"source hierarchy missing declaration: {phrase}")
            rc = 1
        else:
            ok(label)

    canonical_declaration = read_text(ROOT / "docs/governance/CANONICAL_ROADMAP_DECLARATION.md")
    for phrase, label in [
        ("Canonical machine-readable roadmap state: `ROADMAP_CURRENT.json`", "canonical declaration identifies machine-readable state"),
        ("Canonical human-readable roadmap: `ROADMAP_CANONICAL.md`", "canonical declaration identifies human-readable roadmap"),
        ("Derivative roadmap views: `ROADMAP.md`, `docs/ROADMAP.md`", "canonical declaration identifies derivative views"),
        ("Traceability index: `docs/roadmap/roadmap.index.json`", "canonical declaration identifies traceability index"),
        ("`docs/roadmap/roadmap.index.json` is a traceability index and must not declare independent roadmap authority.", "canonical declaration forbids independent index authority"),
    ]:
        if phrase not in canonical_declaration:
            fail(f"canonical declaration missing declaration: {phrase}")
            rc = 1
        else:
            ok(label)

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

    canonical_md = read_text(ROOT / "docs/governance/ROADMAP_CANONICAL.md")
    if "human-readable canonical roadmap" not in canonical_md.lower():
        fail("docs/governance/ROADMAP_CANONICAL.md missing canonical identity declaration")
        rc = 1
    else:
        ok("docs/governance/ROADMAP_CANONICAL.md identity declaration present")

    derived_md = read_text(ROOT / "ROADMAP.md")
    if "non-prevailing" not in derived_md.lower():
        fail("ROADMAP.md must declare itself derivative and non-prevailing")
        rc = 1
    else:
        ok("ROADMAP.md derivative declaration present")

    try:
        roadmap_index = json.loads(read_text(ROOT / "docs/roadmap/roadmap.index.json"))
    except Exception as e:
        fail(f"invalid docs/roadmap/roadmap.index.json: {e}")
        return 1

    if roadmap_index.get("canonical_source") != "ROADMAP_CANONICAL.md":
        fail("roadmap.index.json canonical_source must equal ROADMAP_CANONICAL.md")
        rc = 1
    else:
        ok("roadmap.index.json canonical_source aligned")

    if roadmap_index.get("machine_readable_state") != "ROADMAP_CURRENT.json":
        fail("roadmap.index.json machine_readable_state must equal ROADMAP_CURRENT.json")
        rc = 1
    else:
        ok("roadmap.index.json machine_readable_state aligned")

    if roadmap_index.get("role") != "traceability_index":
        fail("roadmap.index.json role must equal traceability_index")
        rc = 1
    else:
        ok("roadmap.index.json role aligned")

    if roadmap_index.get("authority") != "non-prevailing":
        fail("roadmap.index.json authority must equal non-prevailing")
        rc = 1
    else:
        ok("roadmap.index.json authority aligned")

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
        1 for p in [ROOT / "docs/governance/ROADMAP_CANONICAL.md", ROOT / "CANONICAL_ROADMAP.md"]
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
