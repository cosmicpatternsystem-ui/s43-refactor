import pytest

from governance.decisions import GovernanceDecision, validate_decision


def test_governance_decision_exposes_required_fields():
    decision = GovernanceDecision(
        allowed=True,
        severity="info",
        reason="No risk condition detected",
        rule_id="RG000",
        mode="dry_run",
        metadata={},
        timestamp="2025-01-01T00:00:00+00:00",
    )

    assert decision.allowed is True
    assert decision.severity == "info"
    assert decision.reason == "No risk condition detected"
    assert decision.rule_id == "RG000"
    assert decision.mode == "dry_run"
    assert decision.metadata == {}
    assert decision.timestamp == "2025-01-01T00:00:00+00:00"


@pytest.mark.parametrize("severity", ["info", "warning", "critical"])
def test_validate_decision_allows_expected_severities(severity):
    decision = GovernanceDecision(
        allowed=True,
        severity=severity,
        reason="ok",
        rule_id="RG000",
        mode="dry_run",
        metadata={},
        timestamp="2025-01-01T00:00:00+00:00",
    )
    validate_decision(decision)


@pytest.mark.parametrize("mode", ["dry_run", "enforce", "disabled"])
def test_validate_decision_allows_expected_modes(mode):
    decision = GovernanceDecision(
        allowed=True,
        severity="info",
        reason="ok",
        rule_id="RG000",
        mode=mode,
        metadata={},
        timestamp="2025-01-01T00:00:00+00:00",
    )
    validate_decision(decision)
