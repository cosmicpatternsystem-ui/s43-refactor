from dataclasses import dataclass


ALLOWED_SEVERITIES = {"info", "warning", "critical"}
ALLOWED_MODES = {"dry_run", "enforce", "disabled"}


@dataclass
class GovernanceDecision:
    allowed: bool
    severity: str
    reason: str
    rule_id: str
    mode: str
    metadata: dict
    timestamp: str


def validate_decision(decision: GovernanceDecision) -> None:
    if not isinstance(decision.allowed, bool):
        raise ValueError("allowed must be a bool")

    if not isinstance(decision.severity, str):
        raise ValueError("severity must be a string")
    if decision.severity not in ALLOWED_SEVERITIES:
        raise ValueError("severity is invalid")

    if not isinstance(decision.reason, str):
        raise ValueError("reason must be a string")

    if not isinstance(decision.rule_id, str):
        raise ValueError("rule_id must be a string")

    if not isinstance(decision.mode, str):
        raise ValueError("mode must be a string")
    if decision.mode not in ALLOWED_MODES:
        raise ValueError("mode is invalid")

    if not isinstance(decision.metadata, dict):
        raise ValueError("metadata must be a dict")

    if not isinstance(decision.timestamp, str):
        raise ValueError("timestamp must be a string")
