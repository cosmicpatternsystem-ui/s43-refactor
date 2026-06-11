class _MockExchangeForStress:
    def __init__(self, *, offline_sec: float, support_idempotency: bool = True):
        self._t0 = float(time.time())
        self._offline_until = self._t0 + float(max(0.0, offline_sec))
        self.support_idempotency = bool(support_idempotency)
        self._next_id = 1000
        self._orders: List[dict] = []
        self._by_cid: Dict[str, dict] = {}
    def _new_order(self, symbol: str, side: str, amount: float, price: float, cid: Optional[str]) -> dict:
        oid = str(self._next_id)
        self._next_id += 1
        o = {
            "id": oid,
            "order_id": oid,
            "symbol": _canon_symbol(symbol),
            "side": str(side).lower(),
            "amount": float(amount),
            "price": float(price),
            "status": "open",
        }
        if cid:
            o["client_order_id"] = str(cid)
        self._orders.append(o)
        if cid and self.support_idempotency:
            self._by_cid[str(cid)] = o
        return o
    async def place_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        cid: Optional[str] = None,
        *,
        fill_type: str = "limit",
        market: str = "spot",
        notional_irt: Optional[float] = None,
        reduce_only: Optional[bool] = None,
        **kwargs: Any,
    ) -> dict:
        sym = _canon_symbol(symbol)
        res = await self._ex.place_order(
            symbol=sym,
            side=side,
            amount=amount,
            price=price,
            cid=cid,
            fill_type=fill_type,
            market=market,
            notional_irt=notional_irt,
            reduce_only=reduce_only,
            **kwargs,
        )
        return res