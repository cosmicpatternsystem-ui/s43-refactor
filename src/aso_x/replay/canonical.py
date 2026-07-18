from __future__ import annotations

import json

from aso_x.core.types import FillEvent, PositionState


def _d(value) -> str:
    return str(value)


def state_to_canonical_dict(state: PositionState) -> dict:
    return {
        "quantity": _d(state.quantity),
        "avg_price": _d(state.avg_price),
        "realized_pnl": _d(state.realized_pnl),
        "fees_paid": _d(state.fees_paid),
        "applied_fill_ids": sorted(state.applied_fill_ids),
    }


def fill_to_canonical_dict(fill: FillEvent) -> dict:
    return {
        "fill_id": fill.fill_id,
        "side": fill.side,
        "quantity": _d(fill.quantity),
        "price": _d(fill.price),
        "fee": _d(fill.fee),
    }


def to_canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
