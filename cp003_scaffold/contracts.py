"""Neutral contracts for CP003-A scaffold components."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol


@dataclass(frozen=True)
class SafetyDecision:
    """Conservative policy decision container."""

    allowed: bool = False
    reason: str = "deny_by_default"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PortfolioRecommendation:
    """Neutral recommendation with no execution authority."""

    action: str = "hold"
    confidence: float = 0.0
    rationale: str = "no_op"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AuditReceipt:
    """Simple audit record container."""

    component: str
    status: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationContext:
    """Future-facing context object for pure evaluations."""

    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SafetyLawEvaluator(Protocol):
    """Protocol for safety-law evaluation shells."""

    def evaluate(self, context: EvaluationContext) -> SafetyDecision:
        """Return a conservative decision for the provided context."""


class PortfolioAdvisor(Protocol):
    """Protocol for inert portfolio advisory shells."""

    def recommend(self, context: EvaluationContext) -> PortfolioRecommendation:
        """Return a neutral recommendation for the provided context."""


class AuditReceiptBuilder(Protocol):
    """Protocol for local receipt construction."""

    def build_receipt(self, status: str, **details: Any) -> AuditReceipt:
        """Build an audit receipt without side effects."""