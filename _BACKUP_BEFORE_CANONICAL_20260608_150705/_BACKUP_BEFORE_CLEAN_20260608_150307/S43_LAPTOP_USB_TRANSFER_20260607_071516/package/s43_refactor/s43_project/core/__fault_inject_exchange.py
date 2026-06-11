from .logger import Logger
from .exchange_client import ExchangeClient

class _FaultInjectExchange:
    def __init__(self, ex: ExchangeClient, offline_sec: float, log: logging.Logger):
        self._ex = ex
        self._offline_sec = offline_sec
        self._log = log
        self._in_outage = lambda: time.time() < offline_sec

    async def _place_order_impl(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        cid: Optional[str] = None,
        *,
        notional_irt: Optional[float] = None,
        reduce_only: bool = False,
        fill_type: Optional[str] = None,
        market: Optional[str] = None,
        **kwargs,
    ) -> dict:
        if self._in_outage():
            async def _bg_send():
                try:
                    await self._ex.place_order(
                        symbol,
                        side,
                        amount,
                        price,
                        cid=cid,
                        notional_irt=notional_irt,
                        reduce_only=reduce_only,
                        fill_type=fill_type,
                        market=market,
                        **kwargs,
                    )
                except Exception as e:
                    self._log.error("FaultInjectExchange _bg_send error: %s", e)

            asyncio.create_task(_bg_send())
            raise asyncio.TimeoutError("SIMULATED_RESPONSE_LOSS")

        return await self._ex.place_order(
            symbol,
            side,
            amount,
            price,
            cid=cid,
            notional_irt=notional_irt,
            reduce_only=reduce_only,
            fill_type=fill_type,
            market=market,
            **kwargs,
        )

    async def place_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        cid: Optional[str] = None,
        *,
        notional_irt: Optional[float] = None,
        reduce_only: bool = False,
        fill_type: Optional[str] = None,
        market: Optional[str] = None,
        **kwargs,
    ) -> dict:
        return await self._place_order_impl(
            symbol,
            side,
            amount,
            price,
            cid=cid,
            notional_irt=notional_irt,
            reduce_only=reduce_only,
            fill_type=fill_type,
            market=market,
            **kwargs,
        )

    async def list_orders(self, symbol: Optional[str] = None, status: Optional[str] = None) -> dict:
        return await self._ex.list_orders(symbol=symbol, status=status)

    async def get_depth(self, symbol: str) -> dict:
        return await self._ex.get_depth(symbol)

    async def get_balance(self) -> dict:
        return await self._ex.get_balance()