import sys
import os
import json

# مسیرهای استراتژیک
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_LOG = os.path.join(BASE_DIR, "runtime", "audit", "decision_audit.jsonl")
STOP_FILE = os.path.join(BASE_DIR, "runtime", "EMERGENCY_STOP")

if BASE_DIR not in sys.path: sys.path.insert(0, BASE_DIR)
from core.safety.integrity import verify_audit_chain

def enforce_active_defense():
    """بررسی امنیت زنجیره و توقف فوری در صورت تشخیص نفوذ"""
    if os.path.exists(AUDIT_LOG):
        health = verify_audit_chain(AUDIT_LOG)
        if health["status"] in ["tampered", "corrupted"]:
            with open(STOP_FILE, "w") as f:
                f.write(f"TERMINATED_BY_ACTIVE_DEFENSE: {health['status'].upper()}")
            return False
    return True

if __name__ == "__main__":
    if enforce_active_defense():
        print(json.dumps({"defense_status": "shield_active", "integrity": "nominal"}))
    else:
        print(json.dumps({"defense_status": "emergency_shutdown", "reason": "tamper_detected"}))
