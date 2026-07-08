import sys
import os
sys.path.append(os.getcwd())

from governance.decisions import GovernanceDecision
from governance.risk_guard import RiskGuard, _notify_decision_observer
from governance.policies import RiskThresholdPolicy
from governance.audit_observer import audit_log_observer

def run_test():
    # 1. Setup
    guard = RiskGuard()
    guard.set_decision_observer(audit_log_observer)
    guard.clear_policies()

    # 2. Add Policy: Max 70% risk
    guard.add_policy(RiskThresholdPolicy(max_allowed_risk=0.7))

    # 3. Create high-risk transaction (95%)
    high_risk_dec = GovernanceDecision(
        action_id="TX-999",
        outcome="PENDING",
        reason="Initial request",
        source_rule="USER_TRANSFER",
        actor_id="USER_01",
        context={'risk_score': 0.95},
        timestamp=123456789
    )

    # 4. Process
    print("--- Processing Decision ---")
    final_decision = _notify_decision_observer(high_risk_dec)

    # 5. Verify
    print(f"Resulting Outcome: {final_decision.outcome}")
    print(f"Resulting Reason: {final_decision.reason}")

    if final_decision.outcome == "REJECTED":
        print("\n[VERIFICATION] PASSED: High-risk action was successfully blocked.")
    else:
        print("\n[VERIFICATION] FAILED: Policy was not enforced.")

if __name__ == "__main__":
    run_test()
