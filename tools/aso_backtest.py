import json
import math
import os
import random
import time

from core.safety.integrity import sign_entry

ASSETS = ["BTC", "GOLD", "S&P500", "NVDA", "OIL", "US10Y", "EUR/USD", "COPPER", "LITHIUM", "REITS"]
REPORT_PATH = "runtime/intelligence/backtest_report.json"

def synthetic_history(asset, days=365):
    seed = sum(ord(c) for c in asset)
    rng = random.Random(seed)
    price = 100.0 + (seed % 50)
    history = []

    drift = 0.0002 + ((seed % 7) / 10000)
    volatility = 0.012 + ((seed % 5) / 1000)

    for day in range(days):
        cycle = math.sin(day / 21.0) * 0.003
        shock = rng.uniform(-volatility, volatility)
        price = max(1.0, price * (1.0 + drift + cycle + shock))
        history.append(round(price, 4))

    return history

def moving_average(values, window):
    if len(values) < window:
        return sum(values) / len(values)
    return sum(values[-window:]) / window

def evaluate_asset(asset):
    prices = synthetic_history(asset)
    trades = []
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    correct = 0
    signals = 0

    for i in range(30, len(prices) - 1):
        short_ma = moving_average(prices[i-10:i], 10)
        long_ma = moving_average(prices[i-30:i], 30)
        signal = "BUY" if short_ma > long_ma else "WATCH"
        next_return = (prices[i + 1] - prices[i]) / prices[i]

        if signal == "BUY":
            equity *= (1.0 + next_return)
            trades.append(next_return)
            signals += 1
            if next_return > 0:
                correct += 1

        peak = max(peak, equity)
        drawdown = (peak - equity) / peak if peak else 0.0
        max_drawdown = max(max_drawdown, drawdown)

    win_rate = correct / signals if signals else 0.0
    total_return = equity - 1.0
    verdict = "STRATEGY_VIABLE" if win_rate >= 0.55 and max_drawdown <= 0.25 else "STRATEGY_RISKY"

    return {
        "asset": asset,
        "signals": signals,
        "win_rate": round(win_rate, 4),
        "total_return": round(total_return, 4),
        "max_drawdown": round(max_drawdown, 4),
        "verdict": verdict
    }

def main():
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

    print("--- ASO-X BACKTESTING ENGINE ---")
    results = [evaluate_asset(asset) for asset in ASSETS]

    viable = [r for r in results if r["verdict"] == "STRATEGY_VIABLE"]
    avg_win_rate = sum(r["win_rate"] for r in results) / len(results)

    report = {
        "timestamp": time.time(),
        "engine": "ASO-X Offline Backtesting Engine",
        "method": "deterministic_synthetic_history_moving_average_validation",
        "assets_tested": len(results),
        "average_win_rate": round(avg_win_rate, 4),
        "viable_assets": [r["asset"] for r in viable],
        "results": results
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    for r in results:
        print(
            f"[Backtest] {r['asset']}: "
            f"Win Rate {r['win_rate']:.2%} | "
            f"Return {r['total_return']:.2%} | "
            f"Max DD {r['max_drawdown']:.2%} | "
            f"{r['verdict']}"
        )

    sign_entry({"command": "backtest", "report": REPORT_PATH, "average_win_rate": report["average_win_rate"]}, "backtest_engine")

    print(f"Report: {REPORT_PATH}")
    print("SUCCESS: Backtest completed and audit signed.")

if __name__ == "__main__":
    main()
