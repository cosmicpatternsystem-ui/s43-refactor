import importlib.util
from pathlib import Path


module_path = Path("ops/policy/policy_engine.py")
spec = importlib.util.spec_from_file_location("policy_engine", module_path)
policy_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy_engine)


engine = policy_engine.PolicyEngine(
    rules=[
        policy_engine.MaxNotionalShadowRule(limit=500_000_000.0),
    ]
)

safe_context = policy_engine.PolicyContext(
    symbol="USDTIRT",
    side="BUY",
    qty=1.0,
    price=1.0,
    notional=100_000_000.0,
)

halt_context = policy_engine.PolicyContext(
    symbol="USDTIRT",
    side="BUY",
    qty=1.0,
    price=1.0,
    notional=500_000_001.0,
)

safe_decisions = engine.evaluate(safe_context)
halt_decisions = engine.evaluate(halt_context)

assert safe_decisions[0].action == policy_engine.PolicyAction.ALLOW
assert halt_decisions[0].action == policy_engine.PolicyAction.HALT

print("OK: shadow policy engine evaluated ALLOW and HALT decisions")
