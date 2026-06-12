from datetime import datetime, timezone

from .decisions import GovernanceDecision, validate_decision


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
    return decision


def evaluate_risk(context: dict, mode: str = "dry_run") -> GovernanceDecision:
    if not isinstance(context, dict):
        return _decision(
            allowed=False,
            severity="critical",
            rule_id="RG001",
            reason="invalid_context_type",
            mode=mode,
            metadata={"context_type": type(context).__name__},
        )

    if mode == "disabled":
        return _decision(
            allowed=True,
            severity="info",
            reason="Risk Guard disabled",
            rule_id="RG000",
            mode="disabled",
            metadata={},
        )

    if mode not in {"dry_run", "enforce", "disabled"}:
        return _decision(
            allowed=False,
            severity="warning",
            reason="Invalid mode",
            rule_id="RG001",
            mode="dry_run",
            metadata={"requested_mode": mode},
        )

    if not context:
        return _decision(
            allowed=False,
            severity="warning",
            reason="Missing risk context",
            rule_id="RG001",
            mode="dry_run",
            metadata={},
        )

    exposure = context.get("exposure")
    if exposure is not None and exposure > 1.0:
        return _decision(
            allowed=False,
            severity="warning",
            reason="Abnormal exposure signal detected",
            rule_id="RG002",
            mode="dry_run",
            metadata={"exposure": exposure},
        )

    failure_count = context.get("failure_count")
    if failure_count is not None and failure_count >= 5:
        return _decision(
            allowed=False,
            severity="warning",
            reason="Repeated failure signal detected",
            rule_id="RG003",
            mode="dry_run",
            metadata={"failure_count": failure_count},
        )

    drawdown = context.get("drawdown")
    if drawdown is not None and drawdown >= 0.35:
        return _decision(
            allowed=False,
            severity="critical",
            reason="Critical drawdown signal detected",
            rule_id="RG004",
            mode="dry_run",
            metadata={"drawdown": drawdown},
        )

    return _decision(
        allowed=True,
        severity="info",
        reason="No risk condition detected",
        rule_id="RG000",
        mode="dry_run",
        metadata={},
    )
