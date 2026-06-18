import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


from ops.policy.policy_engine import PolicyContext
from ops.policy.policy_engine_factory import build_policy_engine


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    config = {
        "max_notional": {"enabled": True, "limit": 1000.0},
        "wallet_cycle": {"enabled": True, "window": 10, "max_repeats": 99},
        "operator_override": {"enabled": True, "valid_code": "SMOKE_OVERRIDE"},
    }

    engine = build_policy_engine(config)
    descriptions = engine.describe_rules()
    json.dumps(descriptions, sort_keys=True)

    assert_true(
        descriptions
        == [
            {"rule_id": "shadow.max_notional", "rule_class": "MaxNotionalShadowRule"},
            {"rule_id": "shadow.wallet_cycle", "rule_class": "WalletCycleShadowRule"},
            {"rule_id": "shadow.operator_override", "rule_class": "OperatorOverrideShadowRule"},
        ],
        "factory should build rules in stable order",
    )

    context = PolicyContext(
        symbol="BTCUSDT",
        side="BUY",
        qty=0.01,
        price=50000.0,
        notional=500.0,
        metadata={
            "wallet": "0x123",
            "operator_override_code": "SMOKE_OVERRIDE",
            "fill_type": "limit",
        },
    )
    trace = engine.evaluate_with_trace(context)
    json.dumps(trace, sort_keys=True)

    assert_true(set(trace.keys()) == {"decisions", "final_decision"}, "trace schema should be stable")
    assert_true(len(trace["decisions"]) == 3, "trace should include every configured rule")
    assert_true(
        trace["final_decision"]["policy_action"] == "ALLOW",
        "valid override flow should remain allow in shadow mode",
    )

    try:
        build_policy_engine({"max_notional": {"enabled": True}})
        raise AssertionError("should fail on missing 'limit'")
    except ValueError as exc:
        assert_true("missing required parameter" in str(exc), f"wrong error: {exc}")

    try:
        build_policy_engine({"max_notional": {"limit": "not-a-number"}})
        raise AssertionError("should fail on invalid float")
    except ValueError as exc:
        assert_true("invalid parameter type" in str(exc), f"wrong error: {exc}")

    partial_engine = build_policy_engine(
        {
            "max_notional": {"enabled": True, "limit": 500.0},
            "wallet_cycle": {"enabled": False},
            "operator_override": {"enabled": True, "valid_code": "SMOKE_OVERRIDE"},
        }
    )
    assert_true(
        partial_engine.describe_rules()
        == [
            {"rule_id": "shadow.max_notional", "rule_class": "MaxNotionalShadowRule"},
            {"rule_id": "shadow.operator_override", "rule_class": "OperatorOverrideShadowRule"},
        ],
        "factory should skip disabled rules",
    )

    empty_engine = build_policy_engine({})
    assert_true(len(empty_engine.rules) == 0, "empty config should return empty engine")
    assert_true(empty_engine.describe_rules() == [], "empty config should describe no rules")

    try:
        build_policy_engine({"ghost_rule": {}})
        raise AssertionError("should fail on unknown rule")
    except ValueError as exc:
        assert_true("unknown policy rule" in str(exc), f"wrong error: {exc}")

    print("OK: policy engine factory contract hardened and trace-safe")


if __name__ == "__main__":
    main()
