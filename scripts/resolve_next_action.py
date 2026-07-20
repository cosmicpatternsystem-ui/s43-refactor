#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_ROADMAP = Path("docs/governance/ROADMAP_CURRENT.json")
DEFAULT_CANONICAL = Path("docs/governance/ROADMAP_CANONICAL.md")
DEFAULT_MANIFEST = Path("docs/governance/ROADMAP_MANIFEST.json")
PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

def norm_scalar(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())

def norm_priority(value: Any) -> str:
    v = norm_scalar(value).lower()
    if v in PRIORITY_ORDER:
        return v
    return "low" if v == "" else v

def priority_rank(value: Any) -> int:
    return PRIORITY_ORDER.get(norm_priority(value), 99)

def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing roadmap file: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write_text_atomic(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8-sig", newline="\n")
    tmp.replace(path)

def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]

def entry_title(item: Dict[str, Any]) -> str:
    for key in ("title", "name", "id", "legacy_id", "file"):
        v = norm_scalar(item.get(key))
        if v:
            return v
    return ""

def entry_status(item: Dict[str, Any]) -> str:
    return norm_scalar(item.get("status")).lower()

def entry_depends_on(item: Dict[str, Any]) -> List[str]:
    deps = []
    for dep in as_list(item.get("depends_on")):
        d = norm_scalar(dep)
        if d:
            deps.append(d)
    return deps

def entry_complete(item: Dict[str, Any]) -> bool:
    return entry_status(item) == "complete"

def eligible(items: List[Dict[str, Any]], completed_ids: set[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in items:
        if entry_complete(item):
            continue
        deps = entry_depends_on(item)
        unresolved = [d for d in deps if d not in completed_ids]
        out.append({**item, "_unresolved": unresolved})
    return out

def pick(items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not items:
        return None
    return sorted(
        items,
        key=lambda x: (
            len(x.get("_unresolved") or []),
            priority_rank(x.get("priority")),
            entry_title(x),
        ),
    )[0]

def select_current(data: Dict[str, Any]) -> Dict[str, Any]:
    phases = data.get("phases")
    if not isinstance(phases, list):
        return {
            "status": "INSUFFICIENT_DATA",
            "current_phase": "",
            "current_task": "",
            "current_next_action": "Missing or invalid phases array.",
            "blocked_by": [],
            "selection_reason": "phases_not_list",
            "resolver_version": 1,
        }

    completed_phases = {entry_title(p) for p in phases if entry_complete(p) and entry_title(p)}
    phase_candidates = eligible(phases, completed_phases)

    open_phases = [p for p in phase_candidates if not p.get("_unresolved")]
    blocked_phases = [p for p in phase_candidates if p.get("_unresolved")]

    phase = pick(open_phases) or pick(blocked_phases)
    if not phase:
        return {
            "status": "COMPLETE",
            "current_phase": "",
            "current_task": "",
            "current_next_action": "No remaining roadmap actions.",
            "blocked_by": [],
            "selection_reason": "no_remaining_phases",
            "resolver_version": 1,
        }

    phase_title = entry_title(phase)
    tasks = phase.get("tasks") or phase.get("entries") or []
    if not isinstance(tasks, list):
        tasks = []

    completed_tasks = {entry_title(t) for t in tasks if entry_complete(t) and entry_title(t)}
    task_candidates = eligible(tasks, completed_tasks)

    open_tasks = [t for t in task_candidates if not t.get("_unresolved")]
    blocked_tasks = [t for t in task_candidates if t.get("_unresolved")]

    task = pick(open_tasks) or pick(blocked_tasks)

    if task is None:
        return {
            "status": "PHASE_EMPTY_OR_DONE",
            "current_phase": phase_title,
            "current_task": "",
            "current_next_action": f"Mark phase {phase_title} complete.",
            "blocked_by": phase.get("_unresolved", []),
            "selection_reason": "phase_has_no_tasks",
            "resolver_version": 1,
        }

    task_title = entry_title(task)
    blocked_by = task.get("_unresolved", [])
    if blocked_by:
        status = "BLOCKED"
        reason = "task_dependencies_unresolved"
        action = f"Resolve dependencies for {task_title}: {', '.join(blocked_by)}"
    else:
        status = "READY"
        reason = "next_open_task"
        action = norm_scalar(task.get("next_action") or task.get("description") or task_title)

    return {
        "status": status,
        "current_phase": phase_title,
        "current_task": task_title,
        "current_next_action": action,
        "blocked_by": blocked_by,
        "selection_reason": reason,
        "resolver_version": 1,
    }

def extract_current_markdown(text: str) -> Dict[str, str]:
    phase = ""
    task = ""
    action = ""
    section = ""
    buf: List[str] = []

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            if section == "current next action":
                action = " ".join(buf).strip()
                buf = []
            section = line[3:].strip().lower()
            continue

        if section == "current phase":
            if line.startswith("- Phase:"):
                phase = line.split(":", 1)[1].strip()
            elif line.startswith("- Task:"):
                task = line.split(":", 1)[1].strip()
        elif section == "current next action":
            if line:
                buf.append(line)

    if section == "current next action" and buf:
        action = " ".join(buf).strip()

    return {"current_phase": phase, "current_task": task, "current_next_action": action}

def render_markdown(existing: str, res: Dict[str, Any]) -> str:
    lines = existing.splitlines()
    out: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip().lower()
        if stripped == "## current phase":
            out.append(lines[i])
            out.append(f"- Phase: {res.get('current_phase','')}")
            out.append(f"- Task: {res.get('current_task','')}")
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("## "):
                i += 1
            continue
        if stripped == "## current next action":
            out.append(lines[i])
            out.append(str(res.get("current_next_action","")))
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("## "):
                i += 1
            continue
        out.append(line)
        i += 1

    text = "\n".join(out).rstrip() + "\n"
    return text

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roadmap", default=str(DEFAULT_ROADMAP))
    ap.add_argument("--canonical", default=str(DEFAULT_CANONICAL))
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    roadmap_path = Path(args.roadmap)
    canonical_path = Path(args.canonical)
    manifest_path = Path(args.manifest)

    data = load_json(roadmap_path)
    result = select_current(data)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.write:
        if canonical_path.exists():
            existing = canonical_path.read_text(encoding="utf-8-sig")
        else:
            existing = ""
        if existing:
            updated = render_markdown(existing, result)
        else:
            updated = (
                "# ROADMAP CANONICAL\n\n"
                "## Current Phase\n"
                f"- Phase: {result.get('current_phase','')}\n"
                f"- Task: {result.get('current_task','')}\n\n"
                "## Current Next Action\n"
                f"{result.get('current_next_action','')}\n"
            )
        write_text_atomic(canonical_path, updated)

        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            manifest.setdefault("resolver", {})
            manifest["resolver"].update({
                "name": "scripts/resolve_next_action.py",
                "version": 1,
                "algorithm": "status-dependency-priority-id",
                "output": {
                    "current_phase": result.get("current_phase", ""),
                    "current_task": result.get("current_task", ""),
                    "current_next_action": result.get("current_next_action", ""),
                    "blocked_by": result.get("blocked_by", []),
                }
            })
            write_text_atomic(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        print(f"Updated {canonical_path.as_posix()}")
        return 0

    if args.check:
        if not canonical_path.exists():
            print(f"Missing canonical roadmap: {canonical_path}", file=sys.stderr)
            return 1
        found = extract_current_markdown(canonical_path.read_text(encoding="utf-8-sig"))
        expected = {
            "current_phase": norm_scalar(result.get("current_phase")),
            "current_task": norm_scalar(result.get("current_task")),
            "current_next_action": norm_scalar(result.get("current_next_action")),
        }
        actual = {k: norm_scalar(v) for k, v in found.items()}
        if actual != expected:
            print("Governance Drift: ROADMAP_CANONICAL.md is out of sync.", file=sys.stderr)
            print(json.dumps({"expected": expected, "found": actual}, ensure_ascii=False, indent=2), file=sys.stderr)
            return 1
        print("Governance Audit Passed: Synchronized.")
        return 0

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

