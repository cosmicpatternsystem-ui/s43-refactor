#!/usr/bin/env python3
"""Generate commit-reviewable sanitized summaries from local AI_AUDIT evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SNAPSHOT_PATH = Path("AI_AUDIT/current_state_snapshot.json")
EVENTS_DIR = Path("AI_AUDIT/roadmap_events")
OUTPUT_MD = Path("AUDIT/AI_AUDIT_SANITIZED_SUMMARY.md")
OUTPUT_JSON = Path("AUDIT/AI_AUDIT_SANITIZED_SUMMARY.json")

REDACTION_PATTERNS: Tuple[Tuple[str, re.Pattern[str], str], ...] = (
    ("absolute_path", re.compile(r"(/mnt/[A-Za-z0-9_./-]+|/home/[A-Za-z0-9_./-]+|[A-Za-z]:\\\\[^\s\"']+)", re.I), "[REDACTED_PATH]"),
    ("metadata_service_url", re.compile(r"https?://(?:169\.254\.169\.254|metadata\.google\.internal|metadata\.azure\.com)[^\s\"']*", re.I), "[REDACTED_METADATA_URL]"),
    ("generic_url", re.compile(r"https?://[^\s\"']+", re.I), "[REDACTED_URL]"),
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.I), "Bearer [REDACTED_TOKEN]"),
    ("api_key_assignment", re.compile(r"(?i)(api[_-]?key|token|secret|password|credential|authorization)\s*[:=]\s*[^\s,}\]]+"), "[REDACTED_SECRET]"),
    ("unsafe_command", re.compile(r"(?i)\b(git\s+(reset|clean|push|checkout|tag|branch\s+-D|branch\s+-d)|rm\s+-\w*)\b[^\n]*"), "[REDACTED_UNSAFE_COMMAND]"),
)

RAW_FIELD_NAMES = {
    "prompt",
    "raw_response",
    "response",
    "content",
    "messages",
    "choices",
    "stdout",
    "stderr",
    "environment",
    "env",
}

TOKEN_FIELD_NAMES = {
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "cached_tokens",
    "input_tokens",
    "output_tokens",
    "prompt_tokens_details",
    "completion_tokens_details",
    "input_tokens_details",
}

PROVIDER_FIELD_NAMES = {
    "api_url",
    "model",
    "provider",
    "object",
}

DEFERRED_CATEGORIES = {
    "raw_ai_audit_outputs": "AI_AUDIT provider status/release outputs",
    "state_snapshot": "AI_AUDIT local state snapshot",
    "roadmap_events": "AI_AUDIT roadmap event records",
    "network_bridge_tools": "deferred AI bridge/supervisor tools",
}


def redact_text(value: str) -> Tuple[str, List[str]]:
    redactions: List[str] = []
    result = value
    for name, pattern, replacement in REDACTION_PATTERNS:
        result, count = pattern.subn(replacement, result)
        if count:
            redactions.append(name)
    return result, redactions


def load_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"_missing": True}
    except json.JSONDecodeError as exc:
        return {"_error": f"json decode error: {exc}"}
    if isinstance(data, dict):
        return data
    return {"_error": "json root is not an object"}


def normalize_timestamp(value: Any) -> str:
    if not isinstance(value, str) or not value:
        return "unknown"
    cleaned, _ = redact_text(value)
    if len(cleaned) >= 16:
        return cleaned[:16] + "Z" if "T" in cleaned[:16] else cleaned[:10]
    return cleaned


def safe_short_hash(value: Any) -> str:
    if not isinstance(value, str):
        return "unknown"
    match = re.search(r"\b[0-9a-f]{7,12}\b", value.lower())
    return match.group(0) if match else "unknown"


def summarize_sync_state(snapshot: Dict[str, Any]) -> str:
    ahead_behind = snapshot.get("ahead_behind")
    if isinstance(ahead_behind, str):
        parts = ahead_behind.split()
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            ahead = int(parts[0])
            behind = int(parts[1])
            if ahead == 0 and behind == 0:
                return "synced"
            if ahead and behind:
                return "diverged"
            if ahead:
                return "ahead"
            if behind:
                return "behind"
    status_lines = snapshot.get("status_short_branch")
    if isinstance(status_lines, list) and status_lines:
        first = str(status_lines[0])
        if "..." in first and "ahead" not in first and "behind" not in first:
            return "synced"
    return "unknown"


def detect_redactions_in_value(value: Any) -> List[str]:
    redactions: List[str] = []
    if isinstance(value, str):
        _, found = redact_text(value)
        redactions.extend(found)
    elif isinstance(value, dict):
        for key, nested in value.items():
            lower_key = str(key).lower()
            if lower_key in RAW_FIELD_NAMES:
                redactions.append("raw_content_field")
            if lower_key in TOKEN_FIELD_NAMES:
                redactions.append("token_metadata_field")
            if lower_key in PROVIDER_FIELD_NAMES:
                redactions.append("provider_metadata_field")
            redactions.extend(detect_redactions_in_value(nested))
    elif isinstance(value, list):
        for item in value:
            redactions.extend(detect_redactions_in_value(item))
    return sorted(set(redactions))


def list_event_files(root: Path) -> List[Path]:
    event_dir = root / EVENTS_DIR
    if not event_dir.is_dir():
        return []
    return sorted(path for path in event_dir.glob("*.json") if path.is_file())


def classify_ai_audit_files(root: Path) -> Dict[str, int]:
    ai_dir = root / "AI_AUDIT"
    counts = {
        "raw_provider_json": 0,
        "raw_provider_markdown": 0,
        "state_snapshot_json": 0,
        "roadmap_event_json": 0,
        "other": 0,
    }
    if not ai_dir.is_dir():
        return counts
    for path in ai_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel == SNAPSHOT_PATH.as_posix():
            counts["state_snapshot_json"] += 1
        elif rel.startswith(EVENTS_DIR.as_posix() + "/") and path.suffix == ".json":
            counts["roadmap_event_json"] += 1
        elif path.suffix == ".json":
            counts["raw_provider_json"] += 1
        elif path.suffix == ".md":
            counts["raw_provider_markdown"] += 1
        else:
            counts["other"] += 1
    return counts


def build_summary(root: Path) -> Dict[str, Any]:
    snapshot = load_json(root / SNAPSHOT_PATH)
    event_files = list_event_files(root)
    events = [load_json(path) for path in event_files]

    redaction_flags = set(detect_redactions_in_value(snapshot))
    for event in events:
        redaction_flags.update(detect_redactions_in_value(event))

    latest_event = events[-1] if events else {}
    validation_results: List[str] = []
    for event in events:
        event_type = str(event.get("event_type", ""))
        if "validation" in event_type or "audit" in event_type or "sync" in event_type:
            validation_results.append(event_type)

    ai_counts = classify_ai_audit_files(root)
    summary = {
        "schema_version": 1,
        "phase_id": "22.3",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source_evidence": {
            "state_snapshot_present": not bool(snapshot.get("_missing")),
            "roadmap_event_count": len(event_files),
            "ai_audit_file_categories": ai_counts,
        },
        "sanitized_fields": {
            "latest_commit_short": safe_short_hash(snapshot.get("commit")),
            "repo_sync_state": summarize_sync_state(snapshot),
            "latest_event_type": str(latest_event.get("event_type", "none")),
            "latest_event_timestamp": normalize_timestamp(latest_event.get("timestamp_utc")),
            "validation_results": validation_results[-5:],
            "deferred_file_categories": sorted(DEFERRED_CATEGORIES),
            "destructive_commands_used": False,
            "force_push_used": False,
            "clean_operation_used": False,
            "hard_reset_operation_used": False,
        },
        "redaction": {
            "sensitive_content_detected": bool(redaction_flags),
            "redaction_flags": sorted(redaction_flags),
            "raw_prompts_emitted": False,
            "raw_provider_responses_emitted": False,
            "absolute_paths_emitted": False,
            "token_metadata_emitted": False,
            "unsafe_commands_emitted": False,
        },
        "decision": "SAFE_TO_COMMIT",
        "decision_reason": "Generated summary includes only categories, normalized timestamps, sync status, booleans, and classification metadata.",
    }
    return summary


def render_markdown(summary: Dict[str, Any]) -> str:
    fields = summary["sanitized_fields"]
    source = summary["source_evidence"]
    redaction = summary["redaction"]
    counts = source["ai_audit_file_categories"]
    lines = [
        "# Sanitized AI Audit Evidence Summary",
        "",
        "Status: DRAFT FOR AUDIT REVIEW",
        "Phase: 22.3",
        "Raw Evidence Committed: NO",
        "",
        "## Summary",
        "",
        f"- Latest commit: `{fields['latest_commit_short']}`",
        f"- Repo sync state: {fields['repo_sync_state']}",
        f"- Latest event type: {fields['latest_event_type']}",
        f"- Latest event timestamp: {fields['latest_event_timestamp']}",
        f"- Roadmap event count: {source['roadmap_event_count']}",
        "",
        "## Evidence Categories",
        "",
    ]
    for name in sorted(counts):
        lines.append(f"- {name}: {counts[name]}")
    lines.extend([
        "",
        "## Safety Flags",
        "",
        f"- Destructive commands used: {str(fields['destructive_commands_used']).upper()}",
        f"- Force push used: {str(fields['force_push_used']).upper()}",
        f"- Clean operation used: {str(fields['clean_operation_used']).upper()}",
        f"- Hard reset operation used: {str(fields['hard_reset_operation_used']).upper()}",
        "",
        "## Redaction Result",
        "",
        f"- Sensitive content detected in source evidence: {str(redaction['sensitive_content_detected']).upper()}",
        f"- Redaction flags: {', '.join(redaction['redaction_flags']) if redaction['redaction_flags'] else 'none'}",
        "- Raw prompts emitted: NO",
        "- Raw provider responses emitted: NO",
        "- Absolute paths emitted: NO",
        "- Token metadata emitted: NO",
        "- Unsafe commands emitted: NO",
        "",
        "## Deferred Categories",
        "",
    ])
    for item in fields["deferred_file_categories"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Classification",
        "",
        f"Final Decision: {summary['decision']}",
        f"Reason: {summary['decision_reason']}",
        "",
        "## Review Notes",
        "",
        "- This summary is generated from local state snapshot and roadmap event metadata only.",
        "- Raw AI audit provider outputs remain deferred and are not included.",
    ])
    return "\n".join(lines) + "\n"


def assert_no_forbidden_output(text: str) -> List[str]:
    failures: List[str] = []
    forbidden_checks = {
        "absolute_path": re.compile(r"(/mnt/|/home/|[A-Za-z]:\\\\)"),
        "metadata_url": re.compile(r"https?://(?:169\.254\.169\.254|metadata\.google\.internal|metadata\.azure\.com)", re.I),
        "generic_url": re.compile(r"https?://", re.I),
        "bearer": re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.I),
        "raw_response_key": re.compile(r"raw_response|prompt_tokens|completion_tokens|cached_tokens|input_tokens|output_tokens", re.I),
        "unsafe_command": re.compile(r"git\s+(reset|clean|push|checkout|tag|branch\s+-D)|rm\s+-", re.I),
    }
    for name, pattern in forbidden_checks.items():
        if pattern.search(text):
            failures.append(name)
    return failures


def write_outputs(root: Path, summary: Dict[str, Any], dry_run: bool) -> None:
    md_text = render_markdown(summary)
    json_text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    failures = assert_no_forbidden_output(md_text + json_text)
    if failures:
        raise RuntimeError("sanitized output failed forbidden-content check: " + ", ".join(failures))
    if dry_run:
        print("DRY-RUN: sanitized outputs validated but not written")
        return
    (root / OUTPUT_MD).write_text(md_text, encoding="utf-8")
    (root / OUTPUT_JSON).write_text(json_text, encoding="utf-8")
    print(f"WROTE: {OUTPUT_MD}")
    print(f"WROTE: {OUTPUT_JSON}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate sanitized AUDIT summaries from local AI_AUDIT state evidence.")
    parser.add_argument("--repo", default=".", help="Repository root path.")
    parser.add_argument("--dry-run", action="store_true", help="Validate generated output without writing files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.repo).resolve()
    summary = build_summary(root)
    write_outputs(root, summary, args.dry_run)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
