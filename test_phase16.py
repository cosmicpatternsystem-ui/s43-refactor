import asyncio
import sys
import os

sys.path.append(os.getcwd())

async def test_governance_integration():
    print("--- Starting Phase 16 Integration Test ---")

    try:
        from governance.risk_guard import RiskGuard
        from governance.policies import RiskThresholdPolicy
        from governance.decisions import GovernanceDecision

        rg = RiskGuard()

        if hasattr(rg, "clear_policies"):
            rg.clear_policies()
            print("[INFO] Cleared existing policies.")

        policy = RiskThresholdPolicy(max_allowed_risk=0.5)

        if hasattr(rg, "add_policy"):
            rg.add_policy(policy)
            print("[STEP 1] RiskGuard configured with max_allowed_risk=0.5 via add_policy")
        elif hasattr(rg, "policies"):
            rg.policies.append(policy)
            print("[STEP 1] RiskGuard configured via policies list")
        elif hasattr(rg, "_policies"):
            rg._policies.append(policy)
            print("[STEP 1] RiskGuard configured via _policies list")
        else:
            print("[FAILURE] Could not find a way to register policy on RiskGuard")
            return False

        decision_input = GovernanceDecision(
            action_id="test-phase16-001",
            outcome="PENDING",
            reason="initial",
            actor_id="phase16_test",
            context={
                "type": "place_order",
                "symbol": "BTC/USDT",
                "amount": 1.0,
                "risk_score": 0.8
            }
        )

        print(f"[STEP 2] Simulating high-risk action: Risk={decision_input.context.get('risk_score')}")

        result = rg.validate_action(decision_input)

        outcome = getattr(result, "outcome", "UNKNOWN")
        reason = getattr(result, "reason", "no reason provided")

        if str(outcome).upper() == "REJECTED":
            print(f"[SUCCESS] Governance Veto caught as expected: {reason}")
            print("[RESULT] Phase 16 Integration Logic: VERIFIED")
            return True
        else:
            print(f"[FAILURE] Governance should have blocked this action! Outcome: {outcome}")
            print(f"[DEBUG] reason={reason}")
            return False

    except Exception as e:
        import traceback
        print(f"[ERROR] Test failed with: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_governance_integration())
    sys.exit(0 if result else 1)
