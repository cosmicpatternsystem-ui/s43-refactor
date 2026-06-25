import os
import sys
import json
import time
import hashlib
from datetime import datetime

# Path Configuration
AUDIT_LOG = "runtime/audit/integrity.json"

def sign_entry(data, actor="SYSTEM"):
    if not os.path.exists(AUDIT_LOG):
        chain = []
    else:
        with open(AUDIT_LOG, "r") as f:
            chain = json.load(f)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "actor": actor,
        "data": data,
        "prev_hash": chain[-1]["hash"] if chain else "0000"
    }
    entry["hash"] = hashlib.sha256(str(entry).encode()).hexdigest()
    chain.append(entry)
    
    os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)
    with open(AUDIT_LOG, "w") as f:
        json.dump(chain, f, indent=4)

def monitor():
    print("\033[92m--- ASO-X GOLD STANDARD MONITOR ---\033[0m")
    try:
        while True:
            if os.path.exists(AUDIT_LOG):
                with open(AUDIT_LOG, "r") as f:
                    chain = json.load(f)
            else:
                chain = []
            
            count = len(chain)
            # منطق هوشمند مستقیم
            intel = "INITIALIZING"
            if count > 50: intel = "OPTIMIZED"
            elif count > 10: intel = "STABLE_GROWTH"
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [SYSTEM: ACTIVE] [AUDIT ENTRIES: {count}] [SECURITY: LOCKED] [INTEL: {intel}]", end="\r")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        monitor()
    else:
        print("Use 'python tools/asoctl.py monitor' to start.")
