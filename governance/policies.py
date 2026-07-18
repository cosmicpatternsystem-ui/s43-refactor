from abc import ABC, abstractmethod
from .decisions import GovernanceDecision

class GovernancePolicy(ABC):
    @abstractmethod
    def apply(self, decision: GovernanceDecision) -> GovernanceDecision:
        pass

class RiskThresholdPolicy(GovernancePolicy):
    def __init__(self, max_allowed_risk: float):
        self.max_allowed_risk = max_allowed_risk

    def apply(self, decision):
        """Apply the risk threshold using GovernanceDecision metadata.

        Canonical state is represented by ``allowed``. The dynamically
        exposed ``outcome`` and ``source_rule`` attributes are retained
        for backward compatibility with legacy callers.
        """
        metadata = getattr(decision, "metadata", None)
        if not isinstance(metadata, dict):
            raise TypeError(
                "RiskThresholdPolicy requires decision.metadata to be a dict"
            )

        context = metadata.get("context", {})
        if not isinstance(context, dict):
            raise TypeError(
                "RiskThresholdPolicy requires "
                "decision.metadata['context'] to be a dict"
            )

        risk_score = context.get("risk_score", 0.0)
        if isinstance(risk_score, bool) or not isinstance(
            risk_score, (int, float)
        ):
            raise TypeError(
                "RiskThresholdPolicy requires risk_score to be numeric"
            )

        if risk_score > self.max_allowed_risk:
            decision.allowed = False
            decision.severity = "critical"
            decision.reason = (
                f"Risk score {risk_score} exceeds threshold "
                f"{self.max_allowed_risk}"
            )
            decision.rule_id = "RiskThresholdPolicy"
            decision.outcome = "REJECTED"
            decision.source_rule = "RiskThresholdPolicy"
        else:
            decision.allowed = True
            decision.severity = "info"
            decision.reason = "Risk score within acceptable limits"
            decision.rule_id = "RiskThresholdPolicy"
            decision.outcome = "APPROVED"
            decision.source_rule = "RiskThresholdPolicy"

        return decision
