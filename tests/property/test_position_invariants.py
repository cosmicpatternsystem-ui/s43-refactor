from decimal import Decimal

from hypothesis import given

from aso_x.core.transitions import apply_fill
from aso_x.core.types import PositionState
from tests.property.strategies import fill_events


@given(fill_events())
def test_duplicate_fill_idempotency(fill) -> None:
    state = PositionState()
    s1 = apply_fill(state, fill, risk_limit=Decimal("100"))
    s2 = apply_fill(s1, fill, risk_limit=Decimal("100"))
    assert s1 == s2


@given(fill_events())
def test_risk_limit_preserved_for_single_fill(fill) -> None:
    state = PositionState()
    limit = max(abs(fill.signed_quantity), Decimal("1"))
    next_state = apply_fill(state, fill, risk_limit=limit)
    assert abs(next_state.quantity) <= limit
