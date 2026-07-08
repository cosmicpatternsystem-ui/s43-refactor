from governance.risk_guard import (
    clear_decision_observer,
    evaluate_risk,
    set_decision_observer,
)


def teardown_function():
    clear_decision_observer()


def test_evaluate_risk_notifies_observer_with_decision():
    observed = []

    def observer(decision):
        observed.append(decision)

    set_decision_observer(observer)

    decision = evaluate_risk({"exposure": 0.2}, mode="dry_run")

    assert len(observed) == 1
    assert observed[0] == decision
    assert decision.allowed is True
    assert decision.rule_id == "RG000"


def test_evaluate_risk_without_observer_preserves_behavior():
    clear_decision_observer()

    decision = evaluate_risk({"failure_count": 5}, mode="dry_run")

    assert decision.allowed is False
    assert decision.rule_id == "RG003"
    assert decision.severity == "warning"


def test_observer_failure_does_not_change_governance_behavior():
    def observer(_decision):
        raise RuntimeError("observer failure")

    set_decision_observer(observer)

    decision = evaluate_risk({"drawdown": 0.4}, mode="dry_run")

    assert decision.allowed is False
    assert decision.rule_id == "RG004"
    assert decision.severity == "critical"
