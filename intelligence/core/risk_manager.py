from __future__ import annotations

from intelligence.models.output_contract import RiskAssessment


def assess_risk(symbol: str, price: float) -> RiskAssessment:
    volatility = 0.42
    signal_strength = 0.68

    if volatility >= 0.75:
        risk_level = "HIGH"
    elif volatility >= 0.35:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return RiskAssessment(
        symbol=symbol,
        price=price,
        risk_level=risk_level,
        volatility=volatility,
        signal_strength=signal_strength,
    )


if __name__ == "__main__":
    result = assess_risk("BTC/USDT", 65000.5)
    print(result.to_dict())
