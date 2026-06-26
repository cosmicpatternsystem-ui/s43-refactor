class RiskManager:
    def __init__(self, high_risk_threshold: float = 100000, medium_risk_threshold: float = 10000):
        self.high_risk_threshold = high_risk_threshold
        self.medium_risk_threshold = medium_risk_threshold

    def assess_price_risk(self, symbol: str, price: float) -> dict:
        if price >= self.high_risk_threshold:
            level = "HIGH"
        elif price >= self.medium_risk_threshold:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "symbol": symbol,
            "price": price,
            "risk_level": level,
            "high_threshold": self.high_risk_threshold,
            "medium_threshold": self.medium_risk_threshold,
        }

if __name__ == "__main__":
    manager = RiskManager()
    result = manager.assess_price_risk("BTC/USDT", 65000.5)
    print(result)
