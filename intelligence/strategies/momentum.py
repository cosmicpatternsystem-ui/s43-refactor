from typing import Any, Dict, List
from .base import BaseStrategy
from .registry import StrategyRegistry


@StrategyRegistry.register
class MomentumStrategy(BaseStrategy):
    def name(self) -> str:
        return "momentum_strategy"

    def execute(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        prices = [
            d.get("price")
            for d in data
            if isinstance(d, dict) and d.get("price") is not None
        ]

        if not prices:
            return {
                "strategy": self.name(),
                "signal": "hold",
                "confidence": 0.0,
                "reason": "no_data",
                "metadata": {},
                "status": "ok",
            }

        first_price = prices[0]
        last_price = prices[-1]
        change_pct = ((last_price - first_price) / first_price) if first_price else 0.0

        if last_price > first_price:
            signal = "buy"
            confidence = min(abs(change_pct), 1.0) if first_price else 0.0
        elif last_price < first_price:
            signal = "sell"
            confidence = min(abs(change_pct), 1.0) if first_price else 0.0
        else:
            signal = "hold"
            confidence = 0.0

        return {
            "strategy": self.name(),
            "signal": signal,
            "confidence": confidence,
            "reason": "price_momentum",
            "metadata": {
                "first_price": first_price,
                "last_price": last_price,
                "change_pct": change_pct,
                "sample_size": len(prices),
            },
            "status": "ok",
        }
