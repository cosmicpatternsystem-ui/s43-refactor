from __future__ import annotations

import sys
from pathlib import Path

# اضافه کردن مسیر ریشه به sys.path برای اطمینان از یافتن durable_state
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(REPO_ROOT / "tools"))

try:
    from durable_state import append_audit_event, initialize_schema, integrity_check, utc_now_iso
except ImportError:
    # تلاش مجدد برای وارد کردن مستقیم اگر در پوشه tools هستیم
    from durable_state import append_audit_event, initialize_schema, integrity_check, utc_now_iso

def main() -> None:
    # ۱. اطمینان از آماده بودن اسکیما
    initialize_schema()

    # ۲. چک سلامت فیزیکی دیتابیس قبل از نوشتن
    check = integrity_check()
    if check != "ok":
        print(f"CRITICAL ERROR: SQLite integrity check failed: {check}")
        sys.exit(1)

    # ۳. ثبت پالس در Durable State (بدون لمس کردن JSON)
    event_id = append_audit_event(
        event="GOLD_HEARTBEAT_PULSE",
        status="SUCCESS_DURABLE",
        source="tools/heartbeat.py",
        payload={
            "timestamp": utc_now_iso(),
            "engine": "ASO-X Durable Core v1.1.0",
            "storage_mode": "SQLite/WAL",
            "integrity_verified": True
        },
    )

    print(f"Heartbeat pulse successful. Event ID: {event_id} (Stored in project_memory.sqlite)")

if __name__ == "__main__":
    main()
