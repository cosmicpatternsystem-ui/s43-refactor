from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Protocol


class PolicyAction(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    BLOCK = "BLOCK"
    HALT = "HALT"


@dataclass(frozen=True)
class PolicyContext:
    symbol: str
    side: str
    qty: float
    price: float
    notional: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyDecision:
    action: PolicyAction
    reason: str
    rule_id: str
    details: Dict[str, Any] = field(default_factory=dict)


class PolicyRule(Protocol):
    rule_id: str

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        ...


class MaxNotionalShadowRule:
    rule_id = "shadow.max_notional"

    def __init__(self, limit: float) -> None:
        self.limit = float(limit)

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        if context.notional > self.limit:
            return PolicyDecision(
                action=PolicyAction.HALT,
                reason="notional exceeds shadow limit",
                rule_id=self.rule_id,
                details={"notional": context.notional, "limit": self.limit},
            )

        return PolicyDecision(
            action=PolicyAction.ALLOW,
            reason="notional within shadow limit",
            rule_id=self.rule_id,
            details={"notional": context.notional, "limit": self.limit},
        )


class PolicyEngine:
    def __init__(self, rules: List[PolicyRule] | None = None) -> None:
        self.rules = list(rules or [])

    def evaluate(self, context: PolicyContext) -> List[PolicyDecision]:
        return [rule.evaluate(context) for rule in self.rules]
