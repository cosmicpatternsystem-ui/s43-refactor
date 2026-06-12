import pytest

from governance.risk_guard import evaluate_risk


def test_evaluate_risk_rejects_none_context():
    decision = evaluate_risk(None)

    assert decision.allowed is False
    assert decision.severity == "error"
    assert decision.rule_id == "RG001"
    assert decision.reason == "invalid_context_type"
    assert decision.mode == "dry_run"
    assert decision.metadata["context_type"] == "NoneType"


@pytest.mark.parametrize(
    ("context", "expected_type"),
    [
        ("x", "str"),
        (1, "int"),
        (1.5, "float"),
        ([], "list"),
        ((), "tuple"),
        (object(), "object"),
    ],
)
def test_evaluate_risk_rejects_non_dict_context(context, expected_type):
    decision = evaluate_risk(context)

    assert decision.allowed is False
    assert decision.severity == "error"
    assert decision.rule_id == "RG001"
    assert decision.reason == "invalid_context_type"
    assert decision.mode == "dry_run"
    assert decision.metadata["context_type"] == expected_type
