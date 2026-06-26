from typing import Any, Dict, List
from .base import BaseStrategy
from .registry import StrategyRegistry

@StrategyRegistry.register
class SimpleMovingAverage(BaseStrategy):
    def name(self) -> str:
        return "sma_strategy"

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

        avg = sum(prices) / len(prices)
        last_price = prices[-1]

        if last_price > avg:
            signal = "buy"
            confidence = min(abs(last_price - avg) / avg, 1.0) if avg else 0.0
        elif last_price < avg:
            signal = "sell"
            confidence = min(abs(last_price - avg) / avg, 1.0) if avg else 0.0
        else:
            signal = "hold"
            confidence = 0.0

        return {
            "strategy": self.name(),
            "signal": signal,
            "confidence": confidence,
            "reason": "price_vs_simple_average",
            "metadata": {
                "avg_price": avg,
                "last_price": last_price,
                "sample_size": len(prices),
            },
            "status": "ok",
        }
