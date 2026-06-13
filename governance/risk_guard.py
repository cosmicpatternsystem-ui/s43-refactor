from datetime import datetime, timezone

from .decisions import GovernanceDecision, validate_decision


_DECISION_OBSERVER = None


def set_decision_observer(observer) -> None:
    """Register an optional observation-only governance decision observer."""
    global _DECISION_OBSERVER
    _DECISION_OBSERVER = observer


def clear_decision_observer() -> None:
    """Clear the optional governance decision observer."""
    global _DECISION_OBSERVER
    _DECISION_OBSERVER = None


def _notify_decision_observer(decision: GovernanceDecision) -> None:
    observer = _DECISION_OBSERVER
    if observer is None:
        return

    try:
        observer(decision)
    except Exception:
        # Observation-only hook must never change governance behavior.
        pass


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _decision(
    *,
    allowed: bool,
    severity: str,
    reason: str,
    rule_id: str,
    mode: str,
    metadata: dict | None = None,
) -> GovernanceDecision:
    decision = GovernanceDecision(
        allowed=allowed,
        severity=severity,
        reason=reason,
        rule_id=rule_id,
        mode=mode,
        metadata=metadata or {},
        timestamp=_timestamp(),
    )
    validate_decision(decision)
    _notify_decision_observer(decision)
    return decision


def evaluate_risk(context: dict, mode: str = "dry_run") -> GovernanceDecision:
    """Evaluate a lightweight governance risk decision from context."""

    if not isinstance(context, dict):
        raise TypeError("context must be a dict")

    if mode == "disabled":
        return _decision(
            allowed=True,
            severity="info",
            reason="governance disabled",
            rule_id="RG_DISABLED",
            mode=mode,
            metadata={"context_keys": sorted(context.keys())},
        )

    if mode not in {"dry_run", "enforce"}:
        raise ValueError("invalid mode")

    if not context:
        return _decision(
            allowed=False,
            severity="warning",
            reason="empty context",
            rule_id="RG001",
            mode=mode,
            metadata={},
        )

    exposure = float(context.get("exposure", 0.0))
    if exposure > 1.0:
        return _decision(
            allowed=False,
            severity="critical",
            reason="exposure exceeds limit",
            rule_id="RG002",
            mode=mode,
            metadata={"exposure": exposure},
        )

    failure_count = int(context.get("failure_count", 0))
    if failure_count >= 5:
        return _decision(
            allowed=False,
            severity="warning",
            reason="failure count too high",
            rule_id="RG003",
            mode=mode,
            metadata={"failure_count": failure_count},
        )

    drawdown = float(context.get("drawdown", 0.0))
    if drawdown >= 0.35:
        return _decision(
            allowed=False,
            severity="critical",
            reason="drawdown exceeds threshold",
            rule_id="RG004",
            mode=mode,
            metadata={"drawdown": drawdown},
        )

    return _decision(
        allowed=True,
        severity="info",
        reason="risk acceptable",
        rule_id="RG000",
        mode=mode,
        metadata={
            "exposure": exposure,
            "failure_count": failure_count,
            "drawdown": drawdown,
        },
    )
