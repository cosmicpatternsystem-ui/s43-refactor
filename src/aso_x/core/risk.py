from __future__ import annotations

from decimal import Decimal

from aso_x.core.types import PositionState


def gross_exposure(state: PositionState, mark_price: Decimal) -> Decimal:
    return abs(state.quantity) * Decimal(str(mark_price))


def assert_risk_limit(state: PositionState, risk_limit: Decimal) -> None:
    risk_limit = Decimal(str(risk_limit))
    if abs(state.quantity) > risk_limit:
        raise ValueError(f"risk limit exceeded: abs({state.quantity}) > {risk_limit}")


def assert_gross_limit(state: PositionState, mark_price: Decimal, gross_limit: Decimal) -> None:
    gross_limit = Decimal(str(gross_limit))
    exposure = gross_exposure(state, Decimal(str(mark_price)))
    if exposure > gross_limit:
        raise ValueError(f"gross exposure exceeded: {exposure} > {gross_limit}")
