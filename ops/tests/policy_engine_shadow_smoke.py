#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import pathlib
import sys


def load_policy_engine_module():
    root = pathlib.Path(__file__).resolve().parents[2]
    module_path = root / "ops" / "policy" / "policy_engine.py"
    spec = importlib.util.spec_from_file_location("policy_engine", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load policy engine module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["policy_engine"] = module
    spec.loader.exec_module(module)
    return module


def assert_true(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def main():
    policy_engine = load_policy_engine_module()

    PolicyAction = policy_engine.PolicyAction
    PolicyContext = policy_engine.PolicyContext
    PolicyEngine = policy_engine.PolicyEngine
    MaxNotionalShadowRule = policy_engine.MaxNotionalShadowRule
    WalletCycleShadowRule = policy_engine.WalletCycleShadowRule
    OperatorOverrideShadowRule = policy_engine.OperatorOverrideShadowRule

    engine = PolicyEngine(
        rules=[
            MaxNotionalShadowRule(limit=500_000_000.0),
            WalletCycleShadowRule(window=10, max_repeats=3),
            OperatorOverrideShadowRule(valid_code="SMOKE_OVERRIDE"),
        ]
    )

    safe_context = PolicyContext(
        symbol="USDTIRT",
        side="BUY",
        qty=1000.0,
        price=100000.0,
        notional=100_000_000.0,
        metadata={"wallet": "primary"},
    )

    safe_decisions = engine.evaluate(safe_context)
    safe_final = engine.final_decision(safe_context)

    assert_true(len(safe_decisions) >= 1, "safe_decisions should not be empty")
    assert_true(
        safe_final.action == PolicyAction.ALLOW,
        f"expected ALLOW for safe context, got {safe_final.action}",
    )

    halt_context = PolicyContext(
        symbol="USDTIRT",
        side="BUY",
        qty=5000.0,
        price=100000.0002,
        notional=500_000_001.0,
        metadata={"wallet": "primary"},
    )

    halt_decisions = engine.evaluate(halt_context)
    halt_final = engine.final_decision(halt_context)

    assert_true(
        any(d.action == PolicyAction.HALT for d in halt_decisions),
        "expected at least one HALT decision for max-notional breach",
    )
    assert_true(
        halt_final.action == PolicyAction.HALT,
        f"expected final HALT for halt context, got {halt_final.action}",
    )

    halt_payload = halt_final.to_audit_payload()
    assert_true(halt_payload["policy_action"] == "HALT", "audit payload action mismatch")
    assert_true("policy_reason" in halt_payload, "audit payload missing policy_reason")
    assert_true("policy_rule_id" in halt_payload, "audit payload missing policy_rule_id")
    assert_true("policy_details" in halt_payload, "audit payload missing policy_details")

    wallet_cycle_rule_engine = PolicyEngine(
        rules=[
            WalletCycleShadowRule(window=10, max_repeats=3),
        ]
    )

    wallet_context = PolicyContext(
        symbol="USDTIRT",
        side="BUY",
        qty=1.0,
        price=1000.0,
        notional=1000.0,
        metadata={"wallet": "cycle-wallet-1"},
    )

    first = wallet_cycle_rule_engine.final_decision(wallet_context)
    second = wallet_cycle_rule_engine.final_decision(wallet_context)
    third = wallet_cycle_rule_engine.final_decision(wallet_context)

    assert_true(first.action == PolicyAction.ALLOW, f"1st wallet-cycle expected ALLOW, got {first.action}")
    assert_true(second.action == PolicyAction.ALLOW, f"2nd wallet-cycle expected ALLOW, got {second.action}")
    assert_true(third.action == PolicyAction.HALT, f"3rd wallet-cycle expected HALT, got {third.action}")

    empty_engine = PolicyEngine()
    default_decision = empty_engine.final_decision(safe_context)

    assert_true(
        default_decision.action == PolicyAction.ALLOW,
        f"default decision expected ALLOW, got {default_decision.action}",
    )
    assert_true(
        default_decision.rule_id == "policy.default_allow",
        f"default rule_id mismatch: {default_decision.rule_id}",
    )

    default_payload = default_decision.to_audit_payload()
    assert_true(default_payload["policy_action"] == "ALLOW", "default payload action mismatch")
    assert_true(
        default_payload["policy_rule_id"] == "policy.default_allow",
        "default payload rule_id mismatch",
    )

    override_context = PolicyContext(
        symbol="USDTIRT",
        side="SELL",
        qty=250.0,
        price=100000.0,
        notional=25_000_000.0,
        metadata={
            "wallet": "primary",
            "operator_override": True,
            "operator_override_reason": "manual emergency execution",
            "operator_id": "ops-user-01",
            "operator_override_code": "SMOKE_OVERRIDE",
        },
    )

    override_decisions = engine.evaluate(override_context)
    override_rule_decisions = [
        d for d in override_decisions
        if d.rule_id == "shadow.operator_override"
    ]

    assert_true(
        len(override_rule_decisions) >= 1,
        "expected operator override shadow decision",
    )

    override_decision = override_rule_decisions[0]
    assert_true(
        override_decision.action in (PolicyAction.WARN, PolicyAction.ALLOW),
        f"unexpected operator override action: {override_decision.action}",
    )

    override_payload = override_decision.to_audit_payload()
    assert_true(
        override_payload["policy_rule_id"] == "shadow.operator_override",
        "operator override payload rule_id mismatch",
    )

    print("OK: shadow policy engine evaluated max-notional, wallet-cycle, precedence, default decisions, audit payload, and operator override")


if __name__ == "__main__":
    main()
