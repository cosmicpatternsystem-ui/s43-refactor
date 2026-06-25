import time
import json
import os

# تغییر به فایل اصلی که مانیتور می‌بیند
AUDIT_FILE = "runtime/audit/audit_log.json"

def trigger_heartbeat():
    os.makedirs(os.path.dirname(AUDIT_FILE), exist_ok=True)

    data = [] # مانیتور انتظار لیست یا دیکشنری دارد
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = []

    new_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": "GOLD_HEARTBEAT_PULSE",
        "status": "OPTIMIZED"
    }

    # مدیریت هر دو حالت لیست یا دیکشنری برای سازگاری کامل
    if isinstance(data, list):
        data.append(new_entry)
        count = len(data)
    elif isinstance(data, dict):
        if "entries" not in data: data["entries"] = []
        data["entries"].append(new_entry)
        count = len(data["entries"])
    else:
        data = [new_entry]
        count = 1

    with open(AUDIT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"ASO-X Audit Updated: {count} entries.")

if __name__ == "__main__":
    print("--- ASO-X GOLD SYNC ACTIVE ---")
    while True:
        trigger_heartbeat()
        time.sleep(15)
