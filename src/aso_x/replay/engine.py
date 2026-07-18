from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from aso_x.core.transitions import apply_fill
from aso_x.core.types import FillEvent, PositionState
from aso_x.replay.state_hash import state_hash


@dataclass(frozen=True)
class ReplayResult:
    final_state: PositionState
    final_hash: str


def replay_fills(
    fills: Iterable[FillEvent],
    risk_limit: Decimal,
    initial_state: PositionState | None = None,
) -> ReplayResult:
    state = initial_state or PositionState()
    for fill in fills:
        state = apply_fill(state, fill, risk_limit=risk_limit)
    return ReplayResult(final_state=state, final_hash=state_hash(state))
