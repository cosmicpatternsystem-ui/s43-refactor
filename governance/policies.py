from abc import ABC, abstractmethod
from .decisions import GovernanceDecision

class GovernancePolicy(ABC):
    @abstractmethod
    def apply(self, decision: GovernanceDecision) -> GovernanceDecision:
        pass

class RiskThresholdPolicy(GovernancePolicy):
    def __init__(self, max_allowed_risk: float):
        self.max_allowed_risk = max_allowed_risk

    def apply(self, decision: GovernanceDecision) -> GovernanceDecision:
        # استخراج میزان ریسک از Context تراکنش
        risk_score = decision.context.get("risk_score", 0.0)
        
        if risk_score > self.max_allowed_risk:
            decision.outcome = "REJECTED"
            decision.reason = f"Risk score {risk_score} exceeds threshold {self.max_allowed_risk}"
            decision.source_rule = "RiskThresholdPolicy"
        else:
            decision.outcome = "APPROVED"
            decision.reason = "Risk score within acceptable limits"
        
        return decision
