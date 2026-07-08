import sqlite3
import json
from datetime import datetime
from pathlib import Path

class FinancialDataIngestor:
    def __init__(self, db_path: str = "project_memory.sqlite"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """مطمئن میشود که جداول لازم برای هوش مالی وجود دارند."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS financial_ticks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source TEXT
                )
            ''')
            conn.commit()

    def ingest_price(self, symbol: str, price: float, source: str = "manual"):
        """یک قیمت جدید را در سیستم ثبت میکند."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO financial_ticks (symbol, price, source) VALUES (?, ?, ?)",
                    (symbol.upper(), price, source)
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"Error ingesting data: {e}")
            return False

if __name__ == "__main__":
    # تست اولیه: ثبت قیمت تستی برای بیتکوین
    ingestor = FinancialDataIngestor()
    success = ingestor.ingest_price("BTC/USDT", 65000.50, "ASO-X_TEST")
    if success:
        print("✅ Success: Data ingested into ASO-X Memory.")
    else:
        print("❌ Failed: Data ingestion failed.")
