from datetime import datetime, timezone

import pytest

from governance.decisions import GovernanceDecision, validate_decision


def make_decision(**overrides):
    base = GovernanceDecision(
        allowed=True,
        severity="info",
        reason="No risk condition detected",
        rule_id="RG000",
        mode="dry_run",
        metadata={},
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    data = base.__dict__.copy()
    data.update(overrides)
    return GovernanceDecision(**data)


def test_validate_decision_accepts_valid_decision():
    decision = make_decision()
    validate_decision(decision)


def test_validate_decision_requires_allowed_bool():
    decision = make_decision(allowed="yes")
    with pytest.raises(ValueError):
        validate_decision(decision)


def test_validate_decision_requires_valid_severity():
    decision = make_decision(severity="urgent")
    with pytest.raises(ValueError):
        validate_decision(decision)


def test_validate_decision_requires_valid_mode():
    decision = make_decision(mode="live")
    with pytest.raises(ValueError):
        validate_decision(decision)


def test_validate_decision_requires_string_reason():
    decision = make_decision(reason=123)
    with pytest.raises(ValueError):
        validate_decision(decision)


def test_validate_decision_requires_string_rule_id():
    decision = make_decision(rule_id=999)
    with pytest.raises(ValueError):
        validate_decision(decision)


def test_validate_decision_requires_dict_metadata():
    decision = make_decision(metadata=[])
    with pytest.raises(ValueError):
        validate_decision(decision)


def test_validate_decision_requires_string_timestamp():
    decision = make_decision(timestamp=None)
    with pytest.raises(ValueError):
        validate_decision(decision)
