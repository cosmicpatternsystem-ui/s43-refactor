import time


def governance_audit_logger(decision):
    try:
        timestamp = int(time.time())
        decision_type = getattr(decision, "decision_type", "UNKNOWN_ACTION")
        outcome = getattr(decision, "outcome", "NO_RESULT")
        log_entry = f"[PHASE14] {timestamp} GovernanceDecision:{decision_type} | outcome={outcome}\n"
        with open("governance_audit.log", "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        pass
