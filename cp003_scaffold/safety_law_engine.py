"""Neutral safety-law engine for CP003-A.

This module is intentionally conservative and has no runtime side effects.
"""

from cp003_scaffold.contracts import EvaluationContext, SafetyDecision


class SafetyLawEngine:
    """Conservative placeholder for future safety policy evaluation."""

    def evaluate(self, context: EvaluationContext) -> SafetyDecision:
        """Always deny by default until an authorized integration phase exists."""
        metadata = {
            "symbol": context.symbol,
            "timeframe": context.timeframe,
            "mode": "cp003_a_scaffold",
        }
        return SafetyDecision(
            allowed=False,
            reason="deny_by_default_scaffold",
            metadata=metadata,
        )