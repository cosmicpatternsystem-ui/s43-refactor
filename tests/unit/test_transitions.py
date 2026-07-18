from decimal import Decimal

from aso_x.core.transitions import apply_fill
from aso_x.core.types import FillEvent, PositionState


def test_apply_fill_updates_quantity_and_fee() -> None:
    state = PositionState()
    fill = FillEvent("f1", "BUY", Decimal("2"), Decimal("100"), Decimal("0.5"))
    next_state = apply_fill(state, fill, risk_limit=Decimal("10"))
    assert next_state.quantity == Decimal("2")
    assert next_state.fees_paid == Decimal("0.5")
    assert "f1" in next_state.applied_fill_ids


def test_apply_fill_is_idempotent() -> None:
    state = PositionState()
    fill = FillEvent("f1", "BUY", Decimal("2"), Decimal("100"), Decimal("0.5"))
    once = apply_fill(state, fill, risk_limit=Decimal("10"))
    twice = apply_fill(once, fill, risk_limit=Decimal("10"))
    assert twice == once


def test_apply_fill_realizes_pnl_on_close() -> None:
    state = PositionState()
    open_fill = FillEvent("f1", "BUY", Decimal("2"), Decimal("100"), Decimal("0"))
    close_fill = FillEvent("f2", "SELL", Decimal("1"), Decimal("110"), Decimal("0"))
    s1 = apply_fill(state, open_fill, risk_limit=Decimal("10"))
    s2 = apply_fill(s1, close_fill, risk_limit=Decimal("10"))
    assert s2.quantity == Decimal("1")
    assert s2.realized_pnl == Decimal("10")
