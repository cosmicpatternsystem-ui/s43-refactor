import importlib.util
from pathlib import Path


module_path = Path("ops/policy/policy_engine.py")
spec = importlib.util.spec_from_file_location("policy_engine", module_path)
policy_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy_engine)


engine = policy_engine.PolicyEngine(
    rules=[
        policy_engine.MaxNotionalShadowRule(limit=500_000_000.0),
        policy_engine.WalletCycleShadowRule(window=10, max_repeats=3),
    ]
)

safe_context = policy_engine.PolicyContext(
    symbol="USDTIRT",
    side="BUY",
    qty=1.0,
    price=1.0,
    notional=100_000_000.0,
    metadata={"from_wallet": "wallet_A", "to_wallet": "wallet_B"},
)

halt_context = policy_engine.PolicyContext(
    symbol="USDTIRT",
    side="BUY",
    qty=1.0,
    price=1.0,
    notional=500_000_001.0,
    metadata={"from_wallet": "wallet_A", "to_wallet": "wallet_B"},
)

safe_decisions_1 = engine.evaluate(safe_context)
safe_decisions_2 = engine.evaluate(safe_context)
cycle_decisions = engine.evaluate(safe_context)
halt_decisions = engine.evaluate(halt_context)
final_halt = engine.final_decision(halt_context)
audit_payload = final_halt.to_audit_payload()

assert safe_decisions_1[0].action == policy_engine.PolicyAction.ALLOW
assert safe_decisions_2[1].action == policy_engine.PolicyAction.ALLOW
assert cycle_decisions[1].action == policy_engine.PolicyAction.HALT
assert halt_decisions[0].action == policy_engine.PolicyAction.HALT
assert final_halt.action == policy_engine.PolicyAction.HALT
assert audit_payload["policy_action"] == "HALT"
assert audit_payload["policy_rule_id"] in {
    "shadow.max_notional",
    "shadow.wallet_cycle",
}
assert "policy_reason" in audit_payload
assert "policy_details" in audit_payload

empty_engine = policy_engine.PolicyEngine()
default_decision = empty_engine.final_decision(safe_context)
default_payload = default_decision.to_audit_payload()

assert default_decision.action == policy_engine.PolicyAction.ALLOW
assert default_decision.rule_id == "policy.default_allow"
assert default_payload["policy_action"] == "ALLOW"
assert default_payload["policy_rule_id"] == "policy.default_allow"

print("OK: shadow policy engine evaluated audit-normalized payloads")
