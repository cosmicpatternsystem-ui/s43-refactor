from decimal import Decimal

from hypothesis import given, strategies as st

from aso_x.replay.engine import replay_fills
from tests.property.strategies import fill_events


@given(st.lists(fill_events(), min_size=0, max_size=10))
def test_replay_is_deterministic(fills) -> None:
    r1 = replay_fills(fills, risk_limit=Decimal("100"))
    r2 = replay_fills(fills, risk_limit=Decimal("100"))
    assert r1.final_hash == r2.final_hash
    assert r1.final_state == r2.final_state
