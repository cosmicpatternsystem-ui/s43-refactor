import json
import os
import re
import traceback
from datetime import datetime
from typing import Any

AUDIT_JSONL = os.environ.get("GOVERNANCE_AUDIT_FILE", "governance_audit.jsonl")

_SENSITIVE_PATTERNS = [
    r'(?i)(api[_-]?key\s*[:=]\s*)([^,\s]+)',
    r'(?i)(secret\s*[:=]\s*)([^,\s]+)',
    r'(?i)(token\s*[:=]\s*)([^,\s]+)',
    r'(?i)(password\s*[:=]\s*)([^,\s]+)',
    r'(?i)(passphrase\s*[:=]\s*)([^,\s]+)',
    r'(?i)(signature\s*[:=]\s*)([^,\s]+)',
]

def mask_sensitive_text(value: Any) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        return value

    text = value
    for pattern in _SENSITIVE_PATTERNS:
        text = re.sub(pattern, r'\1********', text)

    if len(text) > 4000:
        text = text[:4000] + "...<truncated>"
    return text

def _mask_deep(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _mask_deep(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_mask_deep(x) for x in obj]
    if isinstance(obj, tuple):
        return tuple(_mask_deep(x) for x in obj)
    if isinstance(obj, set):
        return [_mask_deep(x) for x in obj]
    if isinstance(obj, str):
        return mask_sensitive_text(obj)
    return obj

def append_jsonl(path: str, payload: dict) -> None:
    line = json.dumps(payload, ensure_ascii=False, default=str)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def audit_event(event_type: str, details: Any = None, severity: str = "INFO", phase: str = "17") -> None:
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "severity": severity,
        "phase": phase,
        "details": _mask_deep(details),
    }
    append_jsonl(AUDIT_JSONL, entry)

def audit_exception(event_type: str, exc: Exception, details: Any = None, phase: str = "17") -> None:
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "severity": "ERROR",
        "phase": phase,
        "details": _mask_deep(details),
        "exception_type": type(exc).__name__,
        "exception_message": mask_sensitive_text(str(exc)),
        "traceback": mask_sensitive_text(traceback.format_exc()),
    }
    append_jsonl(AUDIT_JSONL, entry)
