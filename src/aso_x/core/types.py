from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import FrozenSet


def _to_decimal(value: Decimal | str | int | float) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


@dataclass(frozen=True)
class FillEvent:
    fill_id: str
    side: str
    quantity: Decimal
    price: Decimal
    fee: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        object.__setattr__(self, "quantity", _to_decimal(self.quantity))
        object.__setattr__(self, "price", _to_decimal(self.price))
        object.__setattr__(self, "fee", _to_decimal(self.fee))
        if not self.fill_id:
            raise ValueError("fill_id must be non-empty")
        if self.side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.price < 0:
            raise ValueError("price must be non-negative")
        if self.fee < 0:
            raise ValueError("fee must be non-negative")

    @property
    def signed_quantity(self) -> Decimal:
        return self.quantity if self.side == "BUY" else -self.quantity


@dataclass(frozen=True)
class PositionState:
    quantity: Decimal = Decimal("0")
    avg_price: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    fees_paid: Decimal = Decimal("0")
    applied_fill_ids: FrozenSet[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        object.__setattr__(self, "quantity", _to_decimal(self.quantity))
        object.__setattr__(self, "avg_price", _to_decimal(self.avg_price))
        object.__setattr__(self, "realized_pnl", _to_decimal(self.realized_pnl))
        object.__setattr__(self, "fees_paid", _to_decimal(self.fees_paid))
        if self.avg_price < 0:
            raise ValueError("avg_price must be non-negative")
        if self.fees_paid < 0:
            raise ValueError("fees_paid must be non-negative")
