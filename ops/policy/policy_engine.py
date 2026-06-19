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

    def to_audit_payload(self) -> Dict[str, Any]:
        return {
            "policy_action": self.action.value,
            "policy_reason": self.reason,
            "policy_rule_id": self.rule_id,
            "policy_details": dict(self.details),
        }


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



class WalletCycleShadowRule:
    rule_id = "shadow.wallet_cycle"

    def __init__(self, window: int = 10, max_repeats: int = 3) -> None:
        self.window = int(window)
        self.max_repeats = int(max_repeats)
        self.history: List[tuple[Any, ...]] = []

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        signature = self._signature(context)
        self.history.append(signature)

        if len(self.history) > self.window:
            self.history = self.history[-self.window:]

        repeat_count = sum(1 for item in self.history if item == signature)

        if repeat_count >= self.max_repeats:
            return PolicyDecision(
                action=PolicyAction.HALT,
                reason="repeated wallet cycle detected in shadow mode",
                rule_id=self.rule_id,
                details={
                    "symbol": context.symbol,
                    "side": context.side,
                    "repeats": repeat_count,
                    "window": self.window,
                    "wallet_state": signature[-1],
                },
            )

        return PolicyDecision(
            action=PolicyAction.ALLOW,
            reason="wallet cycle within shadow limit",
            rule_id=self.rule_id,
            details={
                "symbol": context.symbol,
                "side": context.side,
                "repeats": repeat_count,
                "window": self.window,
            },
        )

    def _signature(self, context: PolicyContext) -> tuple[Any, ...]:
        wallet_keys = (
            "wallet",
            "wallet_id",
            "source_wallet",
            "destination_wallet",
            "from_wallet",
            "to_wallet",
            "account",
            "subaccount",
        )
        wallet_state = tuple(
            (key, context.metadata.get(key))
            for key in wallet_keys
            if key in context.metadata
        )

        return (
            str(context.symbol).upper(),
            str(context.side).lower(),
            round(float(context.qty), 8),
            round(float(context.price), 2),
            wallet_state,
        )



class OperatorOverrideShadowRule:
    def __init__(self, valid_code: str):
        self.rule_id = "shadow.operator_override"
        self.valid_code = valid_code

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        provided_code = context.metadata.get("operator_override_code")
        if provided_code == self.valid_code:
            return PolicyDecision(
                action=PolicyAction.ALLOW,
                reason="operator override validated",
                rule_id=self.rule_id,
                details={"override": True}
            )
        return PolicyDecision(
            action=PolicyAction.ALLOW,
            reason="no valid operator override provided",
            rule_id=self.rule_id,
            details={"override": False}
        )


class PolicyEngine:
    _precedence = {
        PolicyAction.ALLOW: 0,
        PolicyAction.WARN: 1,
        PolicyAction.BLOCK: 2,
        PolicyAction.HALT: 3,
    }

    def __init__(self, rules: List[PolicyRule] | None = None) -> None:
        self.rules = list(rules or [])


    def describe_rules(self) -> List[Dict[str, str]]:
        return [
            {
                "rule_id": rule.rule_id,
                "rule_class": rule.__class__.__name__,
            }
            for rule in self.rules
        ]

    def evaluate(self, context: PolicyContext) -> List[PolicyDecision]:
        return [rule.evaluate(context) for rule in self.rules]

    def evaluate_with_trace(self, context: PolicyContext) -> Dict[str, Any]:
        decisions = self.evaluate(context)
        final_decision = self._final_decision_from_decisions(decisions)

        return {
            "decisions": [decision.to_audit_payload() for decision in decisions],
            "final_decision": final_decision.to_audit_payload(),
        }

    def _final_decision_from_decisions(self, decisions: List[PolicyDecision]) -> PolicyDecision:
        if not decisions:
            return PolicyDecision(
                action=PolicyAction.ALLOW,
                reason="no policy rules configured",
                rule_id="policy.default_allow",
                details={},
            )

        return max(decisions, key=lambda decision: self._precedence[decision.action])

    def final_decision(self, context: PolicyContext) -> PolicyDecision:
        decisions = self.evaluate(context)
        return self._final_decision_from_decisions(decisions)
