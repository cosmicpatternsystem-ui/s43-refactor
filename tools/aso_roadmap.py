import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from core.safety.integrity import AuditIntegrity

AUDIT_PATH = os.path.join(BASE_DIR, "runtime", "audit", "decision_audit.jsonl")

def audit_event(event, status, detail=None):
    event_data = {
        "project": "ASO",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "roadmap_manager",
        "event": event,
        "status": status,
        "detail": detail or {}
    }
    AuditIntegrity.sign_entry(AUDIT_PATH, event_data)

if __name__ == "__main__":
    # عملکرد ساده برای تست یکپارچگی
    print("ASO Roadmap Manager (Integrity Mode)")
    audit_event("roadmap_manager", "status_check", {"active": True})
