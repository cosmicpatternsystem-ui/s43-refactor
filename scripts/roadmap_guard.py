#!/usr/bin/env python3
"""Roadmap Guard - INVARIANT-ID-001 + INVARIANT-STRUCT-001"""
import json, re, sys
from pathlib import Path

ROADMAP_PATH = Path("docs/governance/ROADMAP_CURRENT.json")
SOURCE_OF_TRUTH = "repository_files_only"
PHASE_PAT  = re.compile(r'^P0-PHASE-\d{2}(?:-\d{2})?-[A-Z0-9-]+$')
TASK_PAT   = re.compile(r'^TASK_\d{2}_\d{2}_\d{2}$')
ALLOWLIST  = {
    'P0-ROADMAP-AUTHORITY', 'P0-POLICY-TRIAD',
    'P0-EVIDENCE-INTEGRITY', 'P0-PHASE-B1-CHECKLIST', 'P0-PHASE-STATUS', }

def validate():
    if not ROADMAP_PATH.exists():
        print(f"[FAIL] Not found: {ROADMAP_PATH}", file=sys.stderr); sys.exit(1)
    data = json.loads(ROADMAP_PATH.read_text(encoding='utf-8'))
    # R1: lifecycle restored to required tuple
    for f in ("schema_version", "roadmap_version", "authority", "lifecycle"):
        if f not in data:
            print(f"[FAIL] Missing: {f}", file=sys.stderr); sys.exit(1)
    if data.get("schema_version") != "2.0":
        print(f"[FAIL] schema_version != 2.0", file=sys.stderr); sys.exit(1)
    if data.get("authority", {}).get("source") != SOURCE_OF_TRUTH:
        print("[FAIL] source_of_truth mismatch", file=sys.stderr); sys.exit(1)
    bad, malformed = [], []
    for idx, item in enumerate(data.get("phases", [])):
        # R2: non-dict items are a structural violation, not silently skipped
        if not isinstance(item, dict):
            malformed.append(f"phases[{idx}]:{type(item).__name__}")
            continue
        v = item.get("id", "")
        if v in ALLOWLIST or PHASE_PAT.fullmatch(v) or TASK_PAT.fullmatch(v):
            continue
        bad.append(v)
    if malformed:
        print(f"[FAIL] INVARIANT-STRUCT-001: non-dict phase items: {malformed}",
              file=sys.stderr); sys.exit(1)
    if bad:
        print(f"[FAIL] INVARIANT-ID-001: {bad}", file=sys.stderr); sys.exit(1)
    print("[OK] Roadmap validation passed")

if __name__ == "__main__":
    validate()


# INVARIANT-ID-001 — canonical phase-id grammar.
# Accepts: P0-PHASE-32-GOVERNANCE, P0-PHASE-33-01-AI-DECISION
# Rejects: shadow short forms (P33-01), embedded newlines, prefix-only matches.
CANONICAL_ID_PATTERN = re.compile(r"P0-PHASE-\d{2}(-\d{2})?(-[A-Z0-9]+)+")

ALLOWED_PHASE_STATUS = {
    "complete", "in_progress", "recorded", "pending",
    "deferred", "abandoned", "blocked", "not_applicable",
    "info", "approved",
}


def _fail_invariant(violations):
    for msg in violations:
        print(msg, file=sys.stderr)
    raise SystemExit(1)


def check_invariant_id_001(roadmap):
    violations = []
    phases = roadmap.get("phases") if isinstance(roadmap, dict) else None
    if not isinstance(phases, list):
        _fail_invariant(["INVARIANT-ID-001: missing or invalid 'phases' registry"])
    seen = set()
    for idx, member in enumerate(phases):
        if not isinstance(member, dict):
            violations.append(f"INVARIANT-ID-001: phase[{idx}] is not an object")
            continue
        pid = member.get("id")
        if not isinstance(pid, str) or not CANONICAL_ID_PATTERN.fullmatch(pid):
            violations.append(f"INVARIANT-ID-001: illegal id {pid!r}")
        else:
            if pid in seen:
                violations.append(f"INVARIANT-ID-001: duplicate id {pid!r}")
            seen.add(pid)
        status = member.get("status")
        if status is not None and status not in ALLOWED_PHASE_STATUS:
            violations.append(f"INVARIANT-ID-001: illegal status {status!r}")
    if violations:
        _fail_invariant(violations)