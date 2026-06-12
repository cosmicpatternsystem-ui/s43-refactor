from governance.risk_guard import evaluate_risk


def test_evaluate_risk_returns_safe_default_for_empty_context():
    decision = evaluate_risk({}, mode="dry_run")

    assert decision.mode == "dry_run"
    assert decision.rule_id == "RG001"
    assert decision.severity == "warning"
    assert decision.allowed is False


def test_evaluate_risk_returns_neutral_decision_when_disabled():
    decision = evaluate_risk({}, mode="disabled")

    assert decision.mode == "disabled"
    assert decision.rule_id == "RG000"
    assert decision.severity == "info"
    assert decision.allowed is True


def test_evaluate_risk_flags_abnormal_exposure():
    context = {"exposure": 1.5}
    decision = evaluate_risk(context, mode="dry_run")

    assert decision.rule_id == "RG002"
    assert decision.severity == "warning"
    assert decision.allowed is False


def test_evaluate_risk_flags_repeated_failures():
    context = {"failure_count": 5}
    decision = evaluate_risk(context, mode="dry_run")

    assert decision.rule_id == "RG003"
    assert decision.severity == "warning"
    assert decision.allowed is False


def test_evaluate_risk_flags_critical_drawdown():
    context = {"drawdown": 0.35}
    decision = evaluate_risk(context, mode="dry_run")

    assert decision.rule_id == "RG004"
    assert decision.severity == "critical"
    assert decision.allowed is False
