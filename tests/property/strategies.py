from decimal import Decimal

from hypothesis import strategies as st

from aso_x.core.types import FillEvent


@st.composite
def fill_events(draw):
    fill_id = draw(st.text(min_size=1, max_size=12))
    side = draw(st.sampled_from(["BUY", "SELL"]))
    quantity = Decimal(str(draw(st.integers(min_value=1, max_value=20))))
    price = Decimal(str(draw(st.integers(min_value=1, max_value=1000))))
    fee = Decimal(str(draw(st.integers(min_value=0, max_value=10))))
    return FillEvent(
        fill_id=fill_id,
        side=side,
        quantity=quantity,
        price=price,
        fee=fee,
    )
