import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


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

    try:
        build_policy_engine({"unknown_rule": {"enabled": True}})
    except ValueError as exc:
        assert_true("unknown policy rule config keys" in str(exc), "unknown rule should fail clearly")
    else:
        raise AssertionError("unknown rule should raise ValueError")

    print("OK: policy engine factory builds stable shadow rule registries")


if __name__ == "__main__":
    main()
