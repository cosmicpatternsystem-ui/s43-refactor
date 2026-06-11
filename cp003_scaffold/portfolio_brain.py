"""Neutral portfolio reasoning facade for CP003-A."""

from cp003_scaffold.contracts import EvaluationContext, PortfolioRecommendation


class PortfolioBrain:
    """Inert recommendation shell with zero execution authority."""

    def recommend(self, context: EvaluationContext) -> PortfolioRecommendation:
        """Return a hold recommendation with zero confidence by default."""
        metadata = {
            "symbol": context.symbol,
            "timeframe": context.timeframe,
            "mode": "cp003_a_scaffold",
        }
        return PortfolioRecommendation(
            action="hold",
            confidence=0.0,
            rationale="no_op_scaffold",
            metadata=metadata,
        )