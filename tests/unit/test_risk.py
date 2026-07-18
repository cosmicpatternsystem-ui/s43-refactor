from decimal import Decimal

import pytest

from aso_x.core.risk import assert_gross_limit, assert_risk_limit, gross_exposure
from aso_x.core.types import PositionState


def test_gross_exposure() -> None:
    state = PositionState(quantity=Decimal("3"))
    assert gross_exposure(state, Decimal("10")) == Decimal("30")


def test_risk_limit_assertion() -> None:
    state = PositionState(quantity=Decimal("5"))
    assert_risk_limit(state, Decimal("5"))
    with pytest.raises(ValueError):
        assert_risk_limit(state, Decimal("4"))


def test_gross_limit_assertion() -> None:
    state = PositionState(quantity=Decimal("3"))
    assert_gross_limit(state, Decimal("10"), Decimal("30"))
    with pytest.raises(ValueError):
        assert_gross_limit(state, Decimal("10"), Decimal("29"))
