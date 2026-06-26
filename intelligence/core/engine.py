from __future__ import annotations

import json
import sqlite3

from intelligence.core.risk_manager import assess_risk
from intelligence.models.output_contract import IntelligenceOutput, MarketAsset


class IntelligenceEngine:
    def __init__(self, db_path: str = "project_memory.sqlite"):
        self.db_path = db_path

    def fetch_latest_ticks(self, limit: int = 10) -> list[tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT symbol, price, source
                FROM financial_ticks
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            return cursor.fetchall()

    def build_market_summary(self, limit: int = 10) -> IntelligenceOutput:
        try:
            rows = self.fetch_latest_ticks(limit=limit)
        except sqlite3.Error as exc:
            return IntelligenceOutput(
                generated_at=IntelligenceOutput.now_timestamp(),
                source="intelligence.core.engine",
                status="error",
                assets=[],
                risk_assessment=[],
                summary=f"Failed to read market data from SQLite: {exc}",
            )

        if not rows:
            return IntelligenceOutput(
                generated_at=IntelligenceOutput.now_timestamp(),
                source="intelligence.core.engine",
                status="empty",
                assets=[],
                risk_assessment=[],
                summary="No market data available.",
            )

        assets = []
        risk_items = []

        for symbol, price, source in rows:
            asset = MarketAsset(symbol=symbol, price=float(price))
            assets.append(asset)
            risk_items.append(assess_risk(asset.symbol, asset.price))

        latest_source = rows[0][2] if rows and len(rows[0]) >= 3 else "financial_ticks"

        return IntelligenceOutput(
            generated_at=IntelligenceOutput.now_timestamp(),
            source=str(latest_source),
            status="ok",
            assets=assets,
            risk_assessment=risk_items,
            summary=f"ASO-X market summary generated successfully from {len(rows)} tick(s).",
        )


def main() -> int:
    engine = IntelligenceEngine()
    output = engine.build_market_summary(limit=10)
    print(json.dumps(output.to_dict(), indent=2, ensure_ascii=False))
    return 0 if output.status in {"ok", "empty"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
