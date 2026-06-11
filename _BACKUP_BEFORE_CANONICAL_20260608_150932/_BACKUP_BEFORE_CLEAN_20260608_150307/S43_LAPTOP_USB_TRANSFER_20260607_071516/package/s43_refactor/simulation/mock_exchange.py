import time
import random
import uuid
from dataclasses import dataclass, field


@dataclass
class MockOrder:
    id: str
    symbol: str
    side: str
    quantity: float
    price: float
    filled: float = 0.0
    status: str = "OPEN"
    timestamp: float = field(default_factory=time.time)


class MockExchange:

    def __init__(self, latency_ms=50, rejection_rate=0.02, slippage=0.001):
        self.latency_ms = latency_ms
        self.rejection_rate = rejection_rate
        self.slippage = slippage
        self.orders = {}
        self.trade_log = []

    def _simulate_latency(self):
        time.sleep(self.latency_ms / 1000)

    def _should_reject(self):
        return random.random() < self.rejection_rate

    def _apply_slippage(self, price):
        slip = price * self.slippage * random.uniform(-1, 1)
        return price + slip

    def place_order(self, symbol, side, quantity, price):
        self._simulate_latency()

        if self._should_reject():
            return {
                "status": "REJECTED",
                "reason": "SIMULATED_REJECTION"
            }

        order_id = str(uuid.uuid4())

        order = MockOrder(
            id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price
        )

        self.orders[order_id] = order

        self._process_fill(order)

        return {
            "status": order.status,
            "order_id": order.id,
            "filled": order.filled,
            "price": order.price
        }

    def _process_fill(self, order):
        fill_ratio = random.uniform(0.4, 1.0)

        filled_qty = order.quantity * fill_ratio
        filled_price = self._apply_slippage(order.price)

        order.filled = filled_qty
        order.price = filled_price

        if filled_qty < order.quantity:
            order.status = "PARTIALLY_FILLED"
        else:
            order.status = "FILLED"

        trade = {
            "order_id": order.id,
            "symbol": order.symbol,
            "side": order.side,
            "quantity": filled_qty,
            "price": filled_price,
            "timestamp": time.time()
        }

        self.trade_log.append(trade)

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def get_trades(self):
        return self.trade_log

    def cancel_order(self, order_id):
        order = self.orders.get(order_id)

        if not order:
            return {"status": "NOT_FOUND"}

        if order.status in ["FILLED", "CANCELLED"]:
            return {"status": "CANNOT_CANCEL"}

        order.status = "CANCELLED"

        return {
            "status": "CANCELLED",
            "order_id": order_id
        }
