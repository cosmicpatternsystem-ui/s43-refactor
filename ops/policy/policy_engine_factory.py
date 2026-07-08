from typing import Any, Dict, List

from ops.policy.policy_engine import (
    MaxNotionalShadowRule,
    OperatorOverrideShadowRule,
    PolicyEngine,
    PolicyRule,
    WalletCycleShadowRule,
)


DEFAULT_RULE_ORDER = ("max_notional", "wallet_cycle", "operator_override")


def _require_config(rule_name: str, rule_config: Dict[str, Any], key: str) -> Any:
    if key not in rule_config:
        raise ValueError(f"missing required parameter for {rule_name}: {key}")
    return rule_config[key]


def _coerce_float(rule_name: str, rule_config: Dict[str, Any], key: str) -> float:
    value = _require_config(rule_name, rule_config, key)
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid parameter type for {rule_name}.{key}: expected float") from exc


def _coerce_int(rule_name: str, rule_config: Dict[str, Any], key: str) -> int:
    value = _require_config(rule_name, rule_config, key)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid parameter type for {rule_name}.{key}: expected int") from exc


def _coerce_str(rule_name: str, rule_config: Dict[str, Any], key: str) -> str:
    value = _require_config(rule_name, rule_config, key)
    if value is None:
        raise ValueError(f"invalid parameter type for {rule_name}.{key}: expected str")
    return str(value)


def build_policy_engine(config: Dict[str, Any] | None = None) -> PolicyEngine:
    config = dict(config or {})
    unknown_rules = set(config) - set(DEFAULT_RULE_ORDER)
    if unknown_rules:
        raise ValueError(f"unknown policy rule config keys: {sorted(unknown_rules)}")

    rules: List[PolicyRule] = []

    for rule_name in DEFAULT_RULE_ORDER:
        rule_config = dict(config.get(rule_name, {}))
        if not rule_config:
            continue

        if rule_config.get("enabled", True) is False:
            continue

        if rule_name == "max_notional":
            rules.append(
                MaxNotionalShadowRule(
                    limit=_coerce_float(rule_name, rule_config, "limit"),
                )
            )
        elif rule_name == "wallet_cycle":
            rules.append(
                WalletCycleShadowRule(
                    window=_coerce_int(rule_name, rule_config, "window"),
                    max_repeats=_coerce_int(rule_name, rule_config, "max_repeats"),
                )
            )
        elif rule_name == "operator_override":
            rules.append(
                OperatorOverrideShadowRule(
                    valid_code=_coerce_str(rule_name, rule_config, "valid_code"),
                )
            )

    return PolicyEngine(rules=rules)
