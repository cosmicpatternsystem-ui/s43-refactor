import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.intelligence.offline_ai import ASOOfflineIntelligence

ASSETS = [
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

def main():
    os.makedirs("runtime/intelligence", exist_ok=True)

    engine = ASOOfflineIntelligence()
    report = engine.generate_report(ASSETS)

    output_path = "runtime/intelligence/offline_ai_report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print("ASO-X INTERNAL AI: ACTIVE")
    print(f"Mode: {report['mode']}")
    print(f"Top Asset: {report['ranked_assets'][0]['asset']}")
    print(f"Recommended Action: {report['ranked_assets'][0]['explanation']['recommended_action']}")
    print(f"Report: {output_path}")

if __name__ == "__main__":
    main()
