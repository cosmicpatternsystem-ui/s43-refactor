# -*- coding: utf-8 -*-
"""
ASO-X Financial Intelligence - Dashboard Health Check
Standard: 50y durability, atomic writes, zero-side-effects on dry-run.
"""
import os
import sys
import json

def verify_system_state():
    required_files = [
        "dashboard/dashboard_bridge.py",
        "dashboard/package.json"
    ]
    status = {}
    for filepath in required_files:
        exists = os.path.exists(filepath)
        status[filepath] = "OK" if exists else "MISSING"
        if not exists:
            print(f"[CRITICAL] Required component missing: {filepath}", file=sys.stderr)
            return False, status
            
    return True, status

if __name__ == "__main__":
    if "--check" in sys.argv:
        success, report = verify_system_state()
        print(json.dumps({"status": "healthy" if success else "unhealthy", "report": report}))
        sys.exit(0 if success else 1)
    
    print("ASO-X Health Check utility. Use --check to run diagnostics.")
    sys.exit(0)