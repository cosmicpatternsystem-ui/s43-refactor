import json
import os
import subprocess
import sys
from datetime import datetime, timezone

# افزودن مسیر ریشه پروژه به پایتون
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from core.safety.integrity import AuditIntegrity

AUDIT_PATH = os.path.join(BASE_DIR, "runtime", "audit", "decision_audit.jsonl")

def audit_event(event, status, detail=None):
    event_data = {
        "project": "ASO",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "supervisor",
        "event": event,
        "status": status,
        "detail": detail or {}
    }
    AuditIntegrity.sign_entry(AUDIT_PATH, event_data)

def run_step(name, command):
    print(f"[{datetime.now(timezone.utc).isoformat()}] running {name}...")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[{name} error]\n{result.stderr}")
    else:
        print(f"{name} stdout:\n{result.stdout}")
    return result

if __name__ == "__main__":
    audit_event("supervisor", "started")
    
    # 1. JSON Guard
    guard = run_step("json_guard", [sys.executable, "tools/aso_json_guard.py"])
    if guard.returncode != 0:
        audit_event("supervisor", "failed", {"step": "json_guard"})
        sys.exit(1)
        
    # 2. Safety Gate
    gate = run_step("safety_gate", [sys.executable, "core/safety/safety_gate.py"])
    if "allowed" not in gate.stdout:
        audit_event("safety_gate", "blocked")
        sys.exit(2)
    
    audit_event("safety_gate", "allowed")
    
    # 3. Engine
    print(f"[{datetime.now(timezone.utc).isoformat()}] starting engine...")
    engine = subprocess.run([sys.executable, "core/autonomy/engine.py"], timeout=10)
    
    audit_event("engine", "finished", {"exit_code": engine.returncode})
    print(f"[{datetime.now(timezone.utc).isoformat()}] supervisor finished successfully")
