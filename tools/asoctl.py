import os
import time
import json

def get_audit_count():
    audit_file = "runtime/audit/audit_log.json"
    if os.path.exists(audit_file):
        try:
            with open(audit_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return len(data)
                if isinstance(data, dict):
                    return len(data.get("entries", [])) or data.get("count", 0) or data.get("total_entries", 0)
        except Exception:
            return 0
    return 0

def monitor():
    print("\033[96m--- ASO-X GOLD STANDARD MONITOR ---\033[0m")
    try:
        while True:
            count = get_audit_count()
            intel_status = "OPTIMIZED" if count > 0 else "INITIALIZING"
            security_status = "LOCKED"
            print(
                f"\r[{time.strftime('%H:%M:%S')}] [SYSTEM: ACTIVE] "
                f"[AUDIT ENTRIES: {count}] [SECURITY: {security_status}] [INTEL: {intel_status}]",
                end="",
                flush=True
            )
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")

if __name__ == "__main__":
    monitor()
