import pytest

from tools.auto_pilot import process_policy_signal
from tools.policy_matrix import PolicyInput


@pytest.fixture
def policy_input():
    return PolicyInput(
        subject="autopilot.execution.loop",
        signal_type="runtime_control_signal",
        severity="high",
        confidence=0.91,
        source="local_smoke_test",
        summary="High-severity financial exposure signal for policy matrix validation.",
        requires_human_review=False,
        tags=["financial_exposure", "real_money", "audit_gap"],
    )


@pytest.fixture
def valid_signal(policy_input):
    return {
        "severity": policy_input.severity,
        "confidence": policy_input.confidence,
        "tags": policy_input.tags,
        "subject": policy_input.subject,
        "source": policy_input.source,
        "signal_type": policy_input.signal_type,
        "summary": policy_input.summary,
        "requires_human_review": policy_input.requires_human_review,
    }


def test_policy_mode_review(monkeypatch, valid_signal):
    monkeypatch.setenv("AP_POLICY_MODE", "review")

    result = process_policy_signal(valid_signal)

    assert result["decision_status"] == "review"


def test_policy_mode_enforce_allows_valid_signal_without_type(monkeypatch, valid_signal):
    monkeypatch.setenv("AP_POLICY_MODE", "enforce")

    result = process_policy_signal(valid_signal)

    assert result["decision_status"] == "allowed"
    assert result["reason_codes"] == ["enforce_allowed_with_policy_review_actions"]


def test_policy_mode_enforce_blocks_invalid_signal(monkeypatch, valid_signal):
    monkeypatch.setenv("AP_POLICY_MODE", "enforce")
    signal = {
        **valid_signal,
        "confidence": 0.0,
        "tags": [],
        "type": "invalid_action_type",
    }

    result = process_policy_signal(signal)

    assert result["decision_status"] == "blocked"
    assert result["reason_codes"] == ["enforce_blocked_invalid_signal"]


def test_policy_matrix_exceptions_block_fail_closed(monkeypatch, valid_signal):
    monkeypatch.setenv("AP_POLICY_MODE", "enforce")
    signal = {
        **valid_signal,
        "severity": None,
    }

    result = process_policy_signal(signal)

    assert result["decision_status"] == "blocked"


def test_policy_result_is_stably_serialized(monkeypatch, valid_signal):
    monkeypatch.setenv("AP_POLICY_MODE", "review")

    result = process_policy_signal(valid_signal)

    assert isinstance(result["policy_result"], dict)