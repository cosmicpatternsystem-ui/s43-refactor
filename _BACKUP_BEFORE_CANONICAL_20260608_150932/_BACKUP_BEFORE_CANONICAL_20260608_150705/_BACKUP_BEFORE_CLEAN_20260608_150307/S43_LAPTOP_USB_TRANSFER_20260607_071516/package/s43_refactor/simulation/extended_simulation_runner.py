import random

from simulation.mock_exchange import MockExchange
from simulation.scenarios.market_scenarios import SCENARIOS


class SimpleStrategy:
    def decide(self, price):
        r = random.random()
        if r < 0.33:
            return "buy"
        elif r < 0.66:
            return "sell"
        return None


def run_simulation(steps=5000, scenario="normal", symbol="BTCUSDT", quantity=1.0):
    exchange = MockExchange()
    strategy = SimpleStrategy()

    market_fn = SCENARIOS.get(scenario)
    if market_fn is None:
        raise ValueError(f"Unknown scenario: {scenario}")

    price = 100.0
    trades = 0
    decisions = 0
    rejected = 0
    partial = 0
    failed = 0

    for step in range(steps):
        price = market_fn(price)
        decision = strategy.decide(price)

        if decision:
            decisions += 1
            try:
                result = exchange.place_order(symbol, decision, quantity, price)

                if isinstance(result, dict):
                    if result.get("filled"):
                        trades += 1
                    if result.get("status") == "rejected":
                        rejected += 1
                    if result.get("partial"):
                        partial += 1
                    if result.get("status") in ("filled", "partial_fill", "accepted"):
                        trades += 0 if result.get("filled") is False else 0
                else:
                    trades += 1

            except Exception:
                failed += 1

    return {
        "scenario": scenario,
        "steps": steps,
        "symbol": symbol,
        "quantity": quantity,
        "decisions": decisions,
        "trades": trades,
        "rejected": rejected,
        "partial": partial,
        "failed": failed,
        "final_price": price,
    }


def main():
    print("PHASE21_EXTENDED_SIMULATION_RUNNER: START")
    print("SAFE-NO-TRADE: ACTIVE")
    print("Exchange: MockExchange only")
    print("-" * 50)

    results = []

    for scenario in SCENARIOS.keys():
        result = run_simulation(
            steps=5000,
            scenario=scenario,
            symbol="BTCUSDT",
            quantity=1.0,
        )
        results.append(result)

        print(f"Scenario: {result['scenario']}")
        print(f"Steps: {result['steps']}")
        print(f"Symbol: {result['symbol']}")
        print(f"Quantity: {result['quantity']}")
        print(f"Decisions: {result['decisions']}")
        print(f"Trades executed: {result['trades']}")
        print(f"Rejected: {result['rejected']}")
        print(f"Partial fills: {result['partial']}")
        print(f"Failed exceptions: {result['failed']}")
        print(f"Final price: {result['final_price']}")
        print("-" * 50)

    total_trades = sum(r["trades"] for r in results)
    total_failed = sum(r["failed"] for r in results)

    print("PHASE21_EXTENDED_SIMULATION_RUNNER: COMPLETE")
    print(f"Total scenarios: {len(results)}")
    print(f"Total trades: {total_trades}")
    print(f"Total failed exceptions: {total_failed}")

    if total_failed == 0:
        print("PHASE21_EXTENDED_SIMULATION: PASS")
    else:
        print("PHASE21_EXTENDED_SIMULATION: REVIEW_REQUIRED")


if __name__ == "__main__":
    main()
