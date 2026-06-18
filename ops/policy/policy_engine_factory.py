from __future__ import annotations

from typing import Any, Dict, List

from ops.policy.policy_engine import (
    MaxNotionalShadowRule,
    OperatorOverrideShadowRule,
    PolicyEngine,
    PolicyRule,
    WalletCycleShadowRule,
)


DEFAULT_RULE_ORDER = ("max_notional", "wallet_cycle", "operator_override")


def build_policy_engine(config: Dict[str, Any] | None = None) -> PolicyEngine:
    config = dict(config or {})

    unknown_rules = set(config) - set(DEFAULT_RULE_ORDER)
    if unknown_rules:
        raise ValueError(f"unknown policy rule config keys: {sorted(unknown_rules)}")

    rules: List[PolicyRule] = []

    for rule_name in DEFAULT_RULE_ORDER:
        if rule_name not in config:
            continue

        rule_config = dict(config[rule_name])
        if rule_config.get("enabled", True) is False:
            continue

        if rule_name == "max_notional":
            rules.append(MaxNotionalShadowRule(limit=float(rule_config["limit"])))
        elif rule_name == "wallet_cycle":
            rules.append(
                WalletCycleShadowRule(
                    window=int(rule_config["window"]),
                    max_repeats=int(rule_config["max_repeats"]),
                )
            )
        elif rule_name == "operator_override":
            rules.append(OperatorOverrideShadowRule(valid_code=str(rule_config["valid_code"])))

    return PolicyEngine(rules=rules)
