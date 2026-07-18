from decimal import Decimal

from aso_x.core.types import FillEvent
from aso_x.replay.engine import replay_fills


def test_golden_replay_smoke() -> None:
    fills = [
        FillEvent("f1", "BUY", Decimal("2"), Decimal("100"), Decimal("1")),
        FillEvent("f2", "SELL", Decimal("1"), Decimal("110"), Decimal("1")),
        FillEvent("f3", "SELL", Decimal("1"), Decimal("90"), Decimal("1")),
    ]
    result = replay_fills(fills, risk_limit=Decimal("10"))
    assert result.final_state.quantity == Decimal("0")
    assert len(result.final_hash) == 64
