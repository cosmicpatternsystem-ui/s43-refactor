from pathlib import Path
import json
import importlib.util


ROOT = Path(__file__).resolve().parents[2]
POLICY_ENGINE_PATH = ROOT / "ops" / "policy" / "policy_engine.py"

spec = importlib.util.spec_from_file_location("policy_engine", POLICY_ENGINE_PATH)
policy_engine = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(policy_engine)


PolicyAction = policy_engine.PolicyAction
PolicyContext = policy_engine.PolicyContext
PolicyDecision = policy_engine.PolicyDecision
PolicyEngine = policy_engine.PolicyEngine
MaxNotionalShadowRule = policy_engine.MaxNotionalShadowRule
WalletCycleShadowRule = policy_engine.WalletCycleShadowRule
OperatorOverrideShadowRule = policy_engine.OperatorOverrideShadowRule


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)



REQUIRED_TRACE_KEYS = {"decisions", "final_decision"}
REQUIRED_DECISION_KEYS = {"policy_rule_id", "policy_action", "policy_reason", "policy_details"}


def assert_serializable_trace(trace):
    json.dumps(trace, sort_keys=True)

    assert set(trace) == REQUIRED_TRACE_KEYS, "trace should expose stable top-level keys"
    assert isinstance(trace["decisions"], list), "trace decisions should be a list"
    assert isinstance(trace["final_decision"], dict), "trace final_decision should be a dict"

    for decision_payload in trace["decisions"] + [trace["final_decision"]]:
        assert set(decision_payload) == REQUIRED_DECISION_KEYS, (
            "decision audit payload should expose stable keys"
        )
        assert isinstance(decision_payload["policy_rule_id"], str), (
            "policy_rule_id should be a string"
        )
        assert isinstance(decision_payload["policy_action"], str), (
            "policy_action should be a string"
        )
        assert isinstance(decision_payload["policy_reason"], str), "policy_reason should be a string"
        assert isinstance(decision_payload["policy_details"], dict), "policy_details should be a dict"


REQUIRED_RULE_DESCRIPTION_KEYS = {"rule_id", "rule_class"}


def assert_serializable_rule_descriptions(rule_descriptions):
    json.dumps(rule_descriptions, sort_keys=True)

    assert isinstance(rule_descriptions, list), "rule descriptions should be a list"
    for rule_description in rule_descriptions:
        assert set(rule_description) == REQUIRED_RULE_DESCRIPTION_KEYS, (
            "rule description should expose stable keys"
        )
        assert isinstance(rule_description["rule_id"], str), "rule_id should be a string"
        assert isinstance(rule_description["rule_class"], str), "rule_class should be a string"

def main():
    safe_context = PolicyContext(
        symbol="BTCUSDT",
        side="BUY",
        qty=0.01,
        price=100.0,
        notional=1.0,
        metadata={"wallet_id": "wallet-a"},
    )

    high_notional_context = PolicyContext(
        symbol="BTCUSDT",
        side="BUY",
        qty=10.0,
        price=1000.0,
        notional=10000.0,
        metadata={"wallet_id": "wallet-a"},
    )

    override_context = PolicyContext(
        symbol="BTCUSDT",
        side="BUY",
        qty=0.01,
        price=100.0,
        notional=1.0,
        metadata={
            "wallet_id": "wallet-a",
            "operator_override_code": "SMOKE_OVERRIDE",
        },
    )

    engine = PolicyEngine(
        rules=[
            MaxNotionalShadowRule(limit=1000.0),
            WalletCycleShadowRule(window=10, max_repeats=99),
            OperatorOverrideShadowRule(valid_code="SMOKE_OVERRIDE"),
        ]
    )

    safe_decisions = engine.evaluate(safe_context)
    assert_true(len(safe_decisions) == 3, "expected all shadow rules to evaluate")
    assert_true(
        all(decision.action == PolicyAction.ALLOW for decision in safe_decisions),
        "safe context should be allowed by all rules",
    )


    assert_true(hasattr(engine, "describe_rules"), "policy engine should expose describe_rules")
    rule_descriptions = engine.describe_rules()
    assert_serializable_rule_descriptions(rule_descriptions)
    assert_true(len(rule_descriptions) == len(engine.rules), "rule descriptions should match rules")
    assert_true(
        rule_descriptions
        == [
            {"rule_id": "shadow.max_notional", "rule_class": "MaxNotionalShadowRule"},
            {"rule_id": "shadow.wallet_cycle", "rule_class": "WalletCycleShadowRule"},
            {"rule_id": "shadow.operator_override", "rule_class": "OperatorOverrideShadowRule"},
        ],
        "rule descriptions should preserve configured rule order",
    )

    safe_trace = engine.evaluate_with_trace(safe_context)
    assert_serializable_trace(safe_trace)
    assert_true(
        [item["policy_rule_id"] for item in safe_trace["decisions"]]
        == [item["rule_id"] for item in rule_descriptions],
        "safe trace decisions should preserve configured rule order",
    )
    assert_true(
        [item["policy_action"] for item in safe_trace["decisions"]] == ["ALLOW", "ALLOW", "ALLOW"],
        "safe trace should preserve each rule decision action",
    )
    assert_true(
        safe_trace["final_decision"]["policy_action"] == "ALLOW",
        "safe trace final decision should remain ALLOW",
    )

    final_halt = engine.final_decision(high_notional_context)
    assert_true(final_halt.action == PolicyAction.HALT, "high notional should HALT")
    assert_true(
        final_halt.rule_id == "shadow.max_notional",
        "HALT should come from max-notional rule",
    )

    final_halt_payload = final_halt.to_audit_payload()
    assert_true(
        final_halt_payload["policy_action"] == "HALT",
        "audit payload should normalize action",
    )
    assert_true(
        final_halt_payload["policy_rule_id"] == "shadow.max_notional",
        "audit payload should include rule id",
    )

    empty_engine = PolicyEngine()

    empty_rule_descriptions = empty_engine.describe_rules()
    assert_serializable_rule_descriptions(empty_rule_descriptions)
    assert_true(empty_rule_descriptions == [], "empty engine should describe no rules")

    default_decision = empty_engine.final_decision(safe_context)
    assert_true(default_decision.action == PolicyAction.ALLOW, "empty engine defaults to ALLOW")
    assert_true(
        default_decision.rule_id == "policy.default_allow",
        "empty engine should use default allow rule id",
    )

    default_payload = default_decision.to_audit_payload()
    assert_true(
        default_payload == {
            "policy_action": "ALLOW",
            "policy_reason": "no policy rules configured",
            "policy_rule_id": "policy.default_allow",
            "policy_details": {},
        },
        "default audit payload should be normalized",
    )

    cycle_engine = PolicyEngine(
        rules=[WalletCycleShadowRule(window=3, max_repeats=3)]
    )
    cycle_engine.evaluate(safe_context)
    cycle_engine.evaluate(safe_context)
    cycle_final = cycle_engine.final_decision(safe_context)
    assert_true(cycle_final.action == PolicyAction.HALT, "wallet cycle should HALT on repeat threshold")
    assert_true(
        cycle_final.rule_id == "shadow.wallet_cycle",
        "wallet cycle HALT should come from wallet-cycle rule",
    )

    override_engine = PolicyEngine(
        rules=[OperatorOverrideShadowRule(valid_code="SMOKE_OVERRIDE")]
    )
    override_final = override_engine.final_decision(override_context)
    assert_true(override_final.action == PolicyAction.ALLOW, "operator override remains ALLOW in shadow mode")
    assert_true(
        override_final.details == {"override": True},
        "operator override should record validated override",
    )

    assert_true(
        hasattr(engine, "evaluate_with_trace"),
        "policy engine should expose evaluate_with_trace",
    )

    trace = engine.evaluate_with_trace(high_notional_context)
    assert_serializable_trace(trace)
    assert_true(isinstance(trace["decisions"], list), "trace decisions should be a list")
    assert_true(
        [item["policy_rule_id"] for item in trace["decisions"]]
        == [item["rule_id"] for item in rule_descriptions],
        "trace decisions should preserve configured rule order",
    )
    assert_true(
        trace["final_decision"] == engine.final_decision(high_notional_context).to_audit_payload(),
        "trace final decision should match final_decision audit payload",
    )
    assert_true(
        trace["final_decision"] == trace["decisions"][0],
        "trace final decision should match highest-precedence rule payload",
    )
    assert_true(
        trace["final_decision"]["policy_action"] == "HALT",
        "trace should preserve HALT final action",
    )
    assert_true(
        trace["decisions"][0]["policy_rule_id"] == "shadow.max_notional",
        "trace should include max-notional rule result in rule order",
    )
    assert_true(
        trace["decisions"][0]["policy_details"] == {"notional": 10000.0, "limit": 1000.0},
        "trace should preserve max-notional HALT details",
    )
    assert_true(
        trace["decisions"][2]["policy_details"] == {"override": False},
        "trace should preserve missing operator override detail",
    )

    empty_trace = empty_engine.evaluate_with_trace(safe_context)
    assert_serializable_trace(empty_trace)
    assert_true(empty_trace["decisions"] == [], "empty trace should have no rule decisions")
    assert_true(
        empty_trace["final_decision"]["policy_action"] == "ALLOW",
        "empty trace should default to ALLOW",
    )
    assert_true(
        empty_trace["final_decision"]["policy_rule_id"] == "policy.default_allow",
        "empty trace should use default allow rule id",
    )
    assert_true(
        empty_trace["final_decision"]["policy_reason"] == "no policy rules configured",
        "empty trace should preserve default allow reason",
    )
    assert_true(
        empty_trace["final_decision"]["policy_details"] == {},
        "empty trace should preserve empty default details",
    )

    override_trace = override_engine.evaluate_with_trace(override_context)
    assert_serializable_trace(override_trace)
    assert_true(
        override_trace["final_decision"]["policy_action"] == "ALLOW",
        "operator override trace should remain ALLOW",
    )
    assert_true(
        override_trace["decisions"][0]["policy_details"] == {"override": True},
        "operator override trace should include override detail",
    )

    print(
        "OK: shadow policy engine evaluated max-notional, wallet-cycle, precedence, "
        "default decisions, audit payload, operator override, structured trace, trace order contract, trace serialization contract, and rule registry introspection"
    )


if __name__ == "__main__":
    main()
