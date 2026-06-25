import time
import subprocess
import sys
import os

print("--- ASO-X HEARTBEAT STARTING ---")
print("Every 15 seconds, a new AI Cycle will be triggered...")

try:
    while True:
        # اجرای چرخه هوش مصنوعی
        subprocess.run([sys.executable, "tools/asoctl.py", "ai-cycle"], env={**os.environ, "PYTHONPATH": "."})
        print("Heartbeat: AI Cycle Triggered and Audited.")
        time.sleep(15)
except KeyboardInterrupt:
    print("Heartbeat stopped.")
