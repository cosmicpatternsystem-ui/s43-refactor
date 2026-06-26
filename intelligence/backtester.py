import sqlite3
import intelligence.strategies
from intelligence.strategies.registry import StrategyRegistry

class Backtester:
    def __init__(self, db_path: str = "project_memory.sqlite"):
        self.db_path = db_path

    def run_strategy(self, strategy_name: str):
        try:
            strategy = StrategyRegistry.get_strategy(strategy_name)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT symbol, price, source FROM financial_ticks LIMIT 100")
            rows = cursor.fetchall()
            conn.close()

            data = [
                {"symbol": r[0], "price": r[1], "source": r[2]}
                for r in rows
                if r[1] is not None
            ]

            if not data:
                return {
                    "strategy": strategy_name,
                    "signal": "hold",
                    "confidence": 0.0,
                    "reason": "empty_dataset",
                    "metadata": {},
                    "status": "empty",
                }

            return strategy.execute(data)

        except ValueError as e:
            return {
                "strategy": strategy_name,
                "signal": "hold",
                "confidence": 0.0,
                "reason": str(e),
                "metadata": {},
                "status": "error",
            }
        except sqlite3.Error as e:
            return {
                "strategy": strategy_name,
                "signal": "hold",
                "confidence": 0.0,
                "reason": f"sqlite_error: {e}",
                "metadata": {},
                "status": "error",
            }
