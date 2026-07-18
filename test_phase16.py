import os
import sys

sys.path.append(os.getcwd())

from governance.risk_guard import RiskGuard
from governance.policies import RiskThresholdPolicy
from governance.decisions import GovernanceDecision


def _build_decision_kwargs(**overrides):
    base = {
        "allowed": True,
        "severity": "low",
        "reason": "initial",
        "rule_id": "phase16_test_rule",
        "mode": "dry_run",
        "metadata": {
            "context": {
                "type": "place_order",
                "symbol": "BTC/USDT",
                "amount": 1.0,
                "risk_score": 0.8,
            }
        },
    }
    base.update(overrides)
    return base


def _add_policy(rg, policy):
    if hasattr(rg, "add_policy"):
        rg.add_policy(policy)
        return

    if hasattr(rg, "policies") and isinstance(rg.policies, list):
        rg.policies.append(policy)
        return

    if hasattr(rg, "_policies") and isinstance(rg._policies, list):
        rg._policies.append(policy)
        return

    raise RuntimeError(
        "RiskGuard does not expose add_policy, policies, or _policies"
    )


def _validate_decision_instance(decision):
    required = (
        "allowed",
        "severity",
        "reason",
        "rule_id",
        "mode",
        "metadata",
    )

    for attr in required:
        if not hasattr(decision, attr):
            raise AssertionError(f"Missing decision attribute: {attr}")

    if not isinstance(decision.metadata, dict):
        raise AssertionError("decision.metadata must be a dict")


def test_governance_integration():
    rg = RiskGuard()

    if hasattr(rg, "clear_policies"):
        rg.clear_policies()

    _add_policy(rg, RiskThresholdPolicy(max_allowed_risk=0.5))

    decision = GovernanceDecision(**_build_decision_kwargs())
    _validate_decision_instance(decision)

    result = rg.validate_action(decision)

    assert result.allowed is False
    assert str(result.reason).strip()

    context = result.metadata.get("context", {})
    assert isinstance(context, dict)
    assert context.get("risk_score") == 0.8


def test_governance_allows_low_risk():
    rg = RiskGuard()

    if hasattr(rg, "clear_policies"):
        rg.clear_policies()

    _add_policy(rg, RiskThresholdPolicy(max_allowed_risk=0.9))

    decision = GovernanceDecision(**_build_decision_kwargs())
    result = rg.validate_action(decision)

    assert result.allowed is True
    assert "risk" in str(result.reason).lower()


def test_governance_handles_missing_context():
    rg = RiskGuard()

    if hasattr(rg, "clear_policies"):
        rg.clear_policies()

    _add_policy(rg, RiskThresholdPolicy(max_allowed_risk=0.5))

    decision = GovernanceDecision(**_build_decision_kwargs(metadata={}))
    result = rg.validate_action(decision)

    assert hasattr(result, "allowed")
    assert isinstance(result.metadata, dict)


if __name__ == "__main__":
    test_governance_integration()
    test_governance_allows_low_risk()
    test_governance_handles_missing_context()
    sys.exit(0)