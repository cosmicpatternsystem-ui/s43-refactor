import os
import sqlite3
import tempfile
import unittest

from intelligence.backtester import Backtester


class BacktesterTests(unittest.TestCase):
    def create_db(self, rows):
        fd, path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)

        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE financial_ticks (
                symbol TEXT,
                price REAL,
                source TEXT
            )
            """
        )
        cursor.executemany(
            "INSERT INTO financial_ticks(symbol, price, source) VALUES (?, ?, ?)",
            rows,
        )
        conn.commit()
        conn.close()
        return path

    def test_run_sma_strategy_returns_ok(self):
        db_path = self.create_db(
            [
                ("BTCUSDT", 100.0, "test"),
                ("BTCUSDT", 110.0, "test"),
                ("BTCUSDT", 120.0, "test"),
            ]
        )
        try:
            bt = Backtester(db_path=db_path)
            result = bt.run_strategy("sma_strategy")
            self.assertEqual(result["strategy"], "sma_strategy")
            self.assertEqual(result["status"], "ok")
            self.assertIn(result["signal"], {"buy", "sell", "hold"})
        finally:
            os.remove(db_path)

    def test_run_momentum_strategy_returns_ok(self):
        db_path = self.create_db(
            [
                ("BTCUSDT", 100.0, "test"),
                ("BTCUSDT", 120.0, "test"),
            ]
        )
        try:
            bt = Backtester(db_path=db_path)
            result = bt.run_strategy("momentum_strategy")
            self.assertEqual(result["strategy"], "momentum_strategy")
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["signal"], "buy")
        finally:
            os.remove(db_path)

    def test_run_invalid_strategy_returns_error(self):
        db_path = self.create_db([("BTCUSDT", 100.0, "test")])
        try:
            bt = Backtester(db_path=db_path)
            result = bt.run_strategy("does_not_exist")
            self.assertEqual(result["status"], "error")
            self.assertIn("not found in registry", result["reason"])
        finally:
            os.remove(db_path)

    def test_run_empty_dataset_returns_empty(self):
        db_path = self.create_db([("BTCUSDT", None, "test")])
        try:
            bt = Backtester(db_path=db_path)
            result = bt.run_strategy("sma_strategy")
            self.assertEqual(result["status"], "empty")
            self.assertEqual(result["signal"], "hold")
        finally:
            os.remove(db_path)


if __name__ == "__main__":
    unittest.main()
