import datetime
from .decisions import GovernanceDecision

def audit_log_observer(decision, *args):
    """Logs governance decisions safely."""
    # اگر به هر دلیلی بیش از یک آرگومان آمد، آرگومان اول که اصل تصمیم است را برمی‌داریم
    if not isinstance(decision, GovernanceDecision) and len(args) > 0:
        if isinstance(args[0], GovernanceDecision):
            decision = args[0]

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[PHASE15] {timestamp} | Action: {decision.action_id} | Outcome: {decision.outcome} | Rule: {decision.source_rule} | Reason: {decision.reason}\n"

    with open("governance_audit.log", "a") as f:
        f.write(log_entry)
