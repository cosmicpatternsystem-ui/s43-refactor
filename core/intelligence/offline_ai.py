import math
import json
import datetime

class ASOOfflineIntelligence:
    """
    Zero-dependency internal intelligence core.
    Produces explainable market decisions from local numeric signals.
    """

    def __init__(self):
        self.version = "ASO-X-OIC-1.0"
        self.risk_limits = {
            "max_single_asset_allocation": 0.20,
            "max_sector_allocation": 0.35,
            "min_cash_reserve": 0.10,
            "max_trade_risk": 0.02
        }

    def normalize(self, value, low, high):
        if high == low:
            return 0.5
        score = (value - low) / (high - low)
        return max(0.0, min(1.0, score))

    def score_asset(self, asset):
        momentum = self.normalize(asset.get("momentum", 0), -100, 100)
        value = self.normalize(asset.get("value_score", 50), 0, 100)
        liquidity = self.normalize(asset.get("liquidity", 50), 0, 100)
        volatility = self.normalize(asset.get("volatility", 50), 0, 100)
        macro = self.normalize(asset.get("macro_score", 50), 0, 100)
        sentiment = self.normalize(asset.get("sentiment", 50), 0, 100)

        risk_penalty = volatility * 0.30
        opportunity = (
            momentum * 0.25 +
            value * 0.20 +
            liquidity * 0.15 +
            macro * 0.25 +
            sentiment * 0.15
        )

        final_score = max(0.0, min(1.0, opportunity - risk_penalty))
        confidence = max(0.05, min(0.95, (liquidity * 0.35) + ((1 - volatility) * 0.35) + (macro * 0.30)))

        return {
            "asset": asset.get("symbol", "UNKNOWN"),
            "score": round(final_score, 4),
            "confidence": round(confidence, 4),
            "risk": round(volatility, 4),
            "explanation": self.explain(asset, final_score, confidence, volatility)
        }

    def explain(self, asset, score, confidence, risk):
        reasons = []
        if asset.get("momentum", 0) > 30:
            reasons.append("positive momentum")
        if asset.get("value_score", 50) > 65:
            reasons.append("attractive valuation")
        if asset.get("liquidity", 50) > 70:
            reasons.append("strong liquidity")
        if asset.get("macro_score", 50) > 65:
            reasons.append("supportive macro conditions")
        if asset.get("volatility", 50) > 70:
            reasons.append("high volatility risk")
        if not reasons:
            reasons.append("mixed or neutral evidence")

        if score >= 0.65 and confidence >= 0.60 and risk <= 0.70:
            action = "ACCUMULATE"
        elif score >= 0.45:
            action = "WATCH"
        elif risk >= 0.75:
            action = "DE_RISK"
        else:
            action = "AVOID"

        return {
            "recommended_action": action,
            "reasons": reasons
        }

    def rank_universe(self, assets):
        ranked = [self.score_asset(asset) for asset in assets]
        ranked.sort(key=lambda x: (x["score"], x["confidence"]), reverse=True)
        return ranked

    def portfolio_weights(self, ranked_assets):
        eligible = [a for a in ranked_assets if a["score"] >= 0.45 and a["risk"] <= 0.75]
        if not eligible:
            return {"cash": 1.0, "positions": []}

        raw_total = sum(a["score"] * a["confidence"] * (1 - a["risk"]) for a in eligible)
        if raw_total <= 0:
            return {"cash": 1.0, "positions": []}

        positions = []
        max_alloc = self.risk_limits["max_single_asset_allocation"]
        cash = self.risk_limits["min_cash_reserve"]

        investable = 1.0 - cash
        for asset in eligible:
            raw_weight = (asset["score"] * asset["confidence"] * (1 - asset["risk"])) / raw_total
            weight = min(max_alloc, raw_weight * investable)
            positions.append({
                "asset": asset["asset"],
                "weight": round(weight, 4),
                "action": asset["explanation"]["recommended_action"],
                "confidence": asset["confidence"]
            })

        used = sum(p["weight"] for p in positions)
        return {
            "cash": round(max(cash, 1.0 - used), 4),
            "positions": positions
        }

    def generate_report(self, assets):
        ranked = self.rank_universe(assets)
        portfolio = self.portfolio_weights(ranked)

        return {
            "engine": self.version,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "mode": "offline_internal_ai",
            "ranked_assets": ranked,
            "portfolio": portfolio,
            "guardrails": self.risk_limits,
            "disclaimer": "Analytical output only. Execution requires governance approval."
        }


if __name__ == "__main__":
    sample_assets = [
        {"symbol": "BTC", "momentum": 45, "value_score": 58, "liquidity": 82, "volatility": 78, "macro_score": 55, "sentiment": 70},
        {"symbol": "GOLD", "momentum": 20, "value_score": 62, "liquidity": 90, "volatility": 30, "macro_score": 75, "sentiment": 60},
        {"symbol": "S&P500", "momentum": 35, "value_score": 50, "liquidity": 95, "volatility": 40, "macro_score": 65, "sentiment": 68},
        {"symbol": "US10Y", "momentum": -10, "value_score": 55, "liquidity": 88, "volatility": 35, "macro_score": 60, "sentiment": 45},
        {"symbol": "OIL", "momentum": 25, "value_score": 57, "liquidity": 80, "volatility": 65, "macro_score": 52, "sentiment": 55},
        {"symbol": "NVDA", "momentum": 70, "value_score": 35, "liquidity": 92, "volatility": 72, "macro_score": 67, "sentiment": 85},
        {"symbol": "EUR/USD", "momentum": 5, "value_score": 50, "liquidity": 98, "volatility": 25, "macro_score": 48, "sentiment": 50},
        {"symbol": "REITS", "momentum": -5, "value_score": 68, "liquidity": 65, "volatility": 55, "macro_score": 42, "sentiment": 45},
        {"symbol": "COPPER", "momentum": 30, "value_score": 61, "liquidity": 75, "volatility": 58, "macro_score": 70, "sentiment": 62},
        {"symbol": "LITHIUM", "momentum": -20, "value_score": 72, "liquidity": 45, "volatility": 85, "macro_score": 66, "sentiment": 40}
    ]

    engine = ASOOfflineIntelligence()
    report = engine.generate_report(sample_assets)

    print(json.dumps(report, indent=4))
