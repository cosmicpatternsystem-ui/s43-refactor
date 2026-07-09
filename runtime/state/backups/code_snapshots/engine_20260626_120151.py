import sqlite3
from pathlib import Path
from risk_manager import RiskManager

class IntelligenceEngine:
    def __init__(self, db_path: str = "project_memory.sqlite"):
        self.db_path = db_path
        self.risk_manager = RiskManager()

    def fetch_latest_ticks(self, limit: int = 10):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                '''
                SELECT symbol, price, volume, timestamp, source
                FROM financial_ticks
                ORDER BY id DESC
                LIMIT ?
                ''',
                (limit,)
            )
            return cursor.fetchall()

    def summarize_market(self):
        rows = self.fetch_latest_ticks(limit=10)
        if not rows:
            return "No market data available."

        lines = ["ASO-X Market Summary with Risk Assessment:"]
        for symbol, price, volume, timestamp, source in rows:
            risk = self.risk_manager.assess_price_risk(symbol, price)
            lines.append(
                f"- {symbol}: price={price}, volume={volume}, time={timestamp}, source={source}, risk={risk['risk_level']}"
            )
        return "\n".join(lines)

if __name__ == "__main__":
    engine = IntelligenceEngine()
    print(engine.summarize_market())
