from governance.risk_guard import evaluate_risk


def test_repeated_failure_signal_blocks_with_rg003():
    decision = evaluate_risk({"failure_count": 5})

    assert decision.allowed is False
    assert decision.severity == "warning"
    assert decision.rule_id == "RG003"
    assert decision.mode == "dry_run"
    assert "Repeated failure" in decision.reason
    assert decision.metadata == {"failure_count": 5}


def test_repeated_failure_below_threshold_allows():
    decision = evaluate_risk({"failure_count": 4})

    assert decision.allowed is True
    assert decision.severity == "info"
    assert decision.rule_id == "RG000"


def test_critical_drawdown_signal_blocks_with_rg004():
    decision = evaluate_risk({"drawdown": 0.35})

    assert decision.allowed is False
    assert decision.severity == "critical"
    assert decision.rule_id == "RG004"
    assert decision.mode == "dry_run"
    assert "Critical drawdown" in decision.reason
    assert decision.metadata == {"drawdown": 0.35}


def test_drawdown_below_threshold_allows():
    decision = evaluate_risk({"drawdown": 0.34})

    assert decision.allowed is True
    assert decision.severity == "info"
    assert decision.rule_id == "RG000"


def test_rule_priority_exposure_before_failure_and_drawdown():
    decision = evaluate_risk({
        "exposure": 1.5,
        "failure_count": 9,
        "drawdown": 0.9,
    })

    assert decision.rule_id == "RG002"
    assert decision.metadata == {"exposure": 1.5}


def test_rule_priority_failure_before_drawdown():
    decision = evaluate_risk({
        "failure_count": 9,
        "drawdown": 0.9,
    })

    assert decision.rule_id == "RG003"
    assert decision.metadata == {"failure_count": 9}
