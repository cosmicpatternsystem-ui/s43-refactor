from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from aso_x.core.risk import assert_risk_limit
from aso_x.core.types import FillEvent, PositionState


def _same_sign(a: Decimal, b: Decimal) -> bool:
    return (a >= 0 and b >= 0) or (a <= 0 and b <= 0)


def apply_fill(state: PositionState, fill: FillEvent, risk_limit: Decimal) -> PositionState:
    if fill.fill_id in state.applied_fill_ids:
        return state

    prev_qty = state.quantity
    signed_qty = fill.signed_quantity
    next_qty = prev_qty + signed_qty

    realized_pnl = state.realized_pnl
    avg_price = state.avg_price

    if prev_qty == 0:
        avg_price = fill.price
    elif _same_sign(prev_qty, next_qty) and _same_sign(prev_qty, signed_qty):
        total_abs = abs(prev_qty) + abs(signed_qty)
        avg_price = (
            Decimal("0")
            if total_abs == 0
            else ((abs(prev_qty) * state.avg_price) + (abs(signed_qty) * fill.price)) / total_abs
        )
    else:
        closing_qty = min(abs(prev_qty), abs(signed_qty))
        if prev_qty > 0:
            realized_pnl += (fill.price - state.avg_price) * closing_qty
        else:
            realized_pnl += (state.avg_price - fill.price) * closing_qty

        if next_qty == 0:
            avg_price = Decimal("0")
        elif _same_sign(prev_qty, next_qty):
            avg_price = state.avg_price
        else:
            avg_price = fill.price

    next_state = replace(
        state,
        quantity=next_qty,
        avg_price=avg_price,
        realized_pnl=realized_pnl,
        fees_paid=state.fees_paid + fill.fee,
        applied_fill_ids=state.applied_fill_ids | frozenset({fill.fill_id}),
    )
    assert_risk_limit(next_state, Decimal(str(risk_limit)))
    return next_state
