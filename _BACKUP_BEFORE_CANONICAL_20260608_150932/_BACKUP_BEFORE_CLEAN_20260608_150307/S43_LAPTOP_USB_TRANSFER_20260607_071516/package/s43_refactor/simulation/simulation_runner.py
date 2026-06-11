import time
import random
import logging
from pathlib import Path
from simulation.mock_exchange import MockExchange

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "simulation_run.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

class MarketDataFeed:
    def __init__(self, start_price=30000):
        self.price = start_price

    def next_tick(self):
        move = random.uniform(-50, 50)
        self.price += move
        return round(self.price, 2)


class SimulationRunner:

    def __init__(self):
        self.exchange = MockExchange()
        self.market = MarketDataFeed()
        self.running = True

    def simple_strategy(self, price):
        if price < 29950:
            return ("BUY", 0.1)
        elif price > 30050:
            return ("SELL", 0.1)
        return None

    def run(self, ticks=200):

        logging.info("SIMULATION_START")

        for i in range(ticks):

            price = self.market.next_tick()
            decision = self.simple_strategy(price)

            logging.info(f"MARKET_TICK price={price}")

            if decision:
                side, qty = decision

                result = self.exchange.place_order(
                    symbol="BTCUSDT",
                    side=side,
                    quantity=qty,
                    price=price
                )

                logging.info(f"ORDER_RESULT {result}")

            time.sleep(0.01)

        logging.info("SIMULATION_END")

        trades = self.exchange.get_trades()

        logging.info(f"TOTAL_TRADES {len(trades)}")

        print("Simulation finished")
        print("Total trades:", len(trades))


if __name__ == "__main__":
    runner = SimulationRunner()
    runner.run()
