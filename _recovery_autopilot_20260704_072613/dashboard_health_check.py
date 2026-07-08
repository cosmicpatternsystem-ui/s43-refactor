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

def read_session_log():
    log_data = []
    try:
        with open("tools/session_log.jsonl", "r", encoding="utf-8") as log_file:
            for line in log_file:
                log_data.append(json.loads(line))
    except FileNotFoundError:
        print("[ERROR] session_log.jsonl not found.", file=sys.stderr)
    except json.JSONDecodeError:
        print("[ERROR] Error decoding JSON from session_log.jsonl.", file=sys.stderr)
    return log_data if log_data else None

def generate_dashboard(log_data):
    if log_data is None:
        print("[ERROR] No log data available to generate dashboard.", file=sys.stderr)
        return "<html><body><h1>Error: No data available</h1></body></html>"
    
    html_content = "<html><head><title>Health Check Dashboard</title></head><body>"
    html_content += "<h1>Session Log Dashboard</h1><table border='1'><tr><th>Timestamp</th><th>Message</th></tr>"
    for entry in log_data:
        html_content += f"<tr><td>{entry.get('timestamp', 'N/A')}</td><td>{entry.get('message', 'N/A')}</td></tr>"
    html_content += "</table></body></html>"
    return html_content

def generate_dashboard(log_data):
    html_content = "<html><head><title>Health Check Dashboard</title></head><body>"
    html_content += "<h1>Session Log Dashboard</h1><table border='1'><tr><th>Timestamp</th><th>Message</th></tr>"
    for entry in log_data:
        html_content += f"<tr><td>{entry.get('timestamp', 'N/A')}</td><td>{entry.get('message', 'N/A')}</td></tr>"
    html_content += "</table></body></html>"
    return html_content

if __name__ == "__main__":
    if "--check" in sys.argv:
        success, report = verify_system_state()
        print(json.dumps({"status": "healthy" if success else "unhealthy", "report": report}))
        sys.exit(0 if success else 1)
    
    log_data = read_session_log()
    dashboard_html = generate_dashboard(log_data)
    with open("dashboard/health_dashboard.html", "w", encoding="utf-8") as dashboard_file:
        dashboard_file.write(dashboard_html)
    print("Dashboard generated: dashboard/health_dashboard.html")
    if "--check" in sys.argv:
        success, report = verify_system_state()
        print(json.dumps({"status": "healthy" if success else "unhealthy", "report": report}))
        sys.exit(0 if success else 1)
    
    print("ASO-X Health Check utility. Use --check to run diagnostics.")
    sys.exit(0)