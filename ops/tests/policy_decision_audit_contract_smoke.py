import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ops.policy.policy_engine import PolicyAction
from ops.policy.policy_engine import PolicyDecision


EXPECTED_PAYLOAD_KEYS = [
    "policy_action",
    "policy_reason",
    "policy_rule_id",
    "policy_details",
]


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def assert_audit_payload_shape(payload):
    json.dumps(payload, sort_keys=True)

    assert_true(
        list(payload.keys()) == EXPECTED_PAYLOAD_KEYS,
        "audit payload should preserve stable key order",
    )
    assert_true(
        set(payload) == set(EXPECTED_PAYLOAD_KEYS),
        "audit payload should expose stable keys",
    )
    assert_true(isinstance(payload["policy_action"], str), "policy_action should be a string")
    assert_true(isinstance(payload["policy_reason"], str), "policy_reason should be a string")
    assert_true(isinstance(payload["policy_rule_id"], str), "policy_rule_id should be a string")
    assert_true(isinstance(payload["policy_details"], dict), "policy_details should be a dict")


def main():
    actions = [
        PolicyAction.ALLOW,
        PolicyAction.WARN,
        PolicyAction.BLOCK,
        PolicyAction.HALT,
    ]

    for action in actions:
        decision = PolicyDecision(
            action=action,
            reason=f"{action.value.lower()} reason",
            rule_id=f"contract.{action.value.lower()}",
            details={
                "action": action.value,
                "threshold": 10.5,
                "count": 2,
                "enabled": True,
                "tags": ["contract", "audit"],
            },
        )
        payload = decision.to_audit_payload()

        assert_audit_payload_shape(payload)
        assert_true(
            payload
            == {
                "policy_action": action.value,
                "policy_reason": f"{action.value.lower()} reason",
                "policy_rule_id": f"contract.{action.value.lower()}",
                "policy_details": {
                    "action": action.value,
                    "threshold": 10.5,
                    "count": 2,
                    "enabled": True,
                    "tags": ["contract", "audit"],
                },
            },
            f"{action.value} audit payload should be normalized",
        )

    empty_details_decision = PolicyDecision(
        action=PolicyAction.ALLOW,
        reason="empty details",
        rule_id="contract.empty_details",
    )
    empty_payload = empty_details_decision.to_audit_payload()
    assert_audit_payload_shape(empty_payload)
    assert_true(
        empty_payload["policy_details"] == {},
        "default decision details should serialize as an empty dict",
    )

    source_details = {"limit": 1000.0, "notional": 1500.0}
    copy_decision = PolicyDecision(
        action=PolicyAction.HALT,
        reason="copy details",
        rule_id="contract.copy_details",
        details=source_details,
    )
    copy_payload = copy_decision.to_audit_payload()
    copy_payload["policy_details"]["limit"] = 1.0

    assert_true(
        copy_decision.details == {"limit": 1000.0, "notional": 1500.0},
        "audit payload should not mutate decision details",
    )
    assert_true(
        source_details == {"limit": 1000.0, "notional": 1500.0},
        "audit payload should not mutate source details",
    )

    print(
        "OK: policy decision audit payload contract preserves action normalization, stable keys, serialization, default details, and copy safety"
    )


if __name__ == "__main__":
    main()
