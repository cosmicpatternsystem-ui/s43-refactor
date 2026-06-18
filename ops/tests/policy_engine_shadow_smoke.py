import importlib.util
from pathlib import Path

module_path = Path("ops/policy/policy_engine.py")
spec = importlib.util.spec_from_file_location("policy_engine", module_path)
policy_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy_engine)

engine = policy_engine.PolicyEngine(
    rules=[
        policy_engine.MaxNotionalShadowRule(limit=500_000_000.0),
        policy_engine.OperatorOverrideShadowRule(valid_code="SUPER-SECRET-123")
    ]
)

# Case 1: Large order WITH override
override_context = policy_engine.PolicyContext(
    symbol="USDTIRT", side="BUY", qty=1.0, price=1.0,
    notional=900_000_000.0,
    metadata={"operator_override_code": "SUPER-SECRET-123"}
)

decisions = engine.evaluate(override_context)
actions = [d.action for d in decisions]
rule_ids = [d.rule_id for d in decisions]

assert policy_engine.PolicyAction.ALLOW in actions
assert "shadow.operator_override" in rule_ids
# Note: MaxNotional will still return HALT in its own decision
assert policy_engine.PolicyAction.HALT in actions

print("OK: shadow policy engine evaluated operator override")
