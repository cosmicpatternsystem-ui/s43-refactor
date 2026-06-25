# Production Deployment Guide
1. Ensure G:\ drive or equivalent persistent volume is mapped for audit logs.
2. Run 'asoctl.py' to verify integrity chain before startup.
3. Deploy Heartbeat as a background service (Systemd/Windows Service).
4. Connect Enterprise SIEM to runtime/audit/audit_log.json.
