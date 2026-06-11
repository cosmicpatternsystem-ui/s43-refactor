from .orch22_market_state import Orch22MarketState
from .order_journal import OrderJournal
from .orch22_orchestrator import Orch22Orchestrator
from .logger import Logger
from .__orch22_stale_clock import _Orch22StaleClock
from .exchange_client import ExchangeClient
from .__orch22_async_component import _Orch22AsyncComponent
from .bot_config import BotConfig
from .orch22_wallet_state import Orch22WalletState

class Orch22WalletEngine(_Orch22AsyncComponent):
    def __init__(self, *, name: str, client: "ExchangeClient", cfg: "BotConfig", log: logging.Logger) -> None:
        self.name = name
        self.client = client
        self.cfg = cfg
        self._log = log
        self.state = Orch22WalletState(name=name)
        self._stop = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        self._fresh = _Orch22StaleClock()
        self.balance_refresh_sec = float(_env_float("ORCH22_BAL_REFRESH_SEC", getattr(cfg, "balance_refresh_sec", 8.0)) or 8.0)
        self.orders_refresh_sec = float(_env_float("ORCH22_ORD_REFRESH_SEC", getattr(cfg, "orders_refresh_sec", 3.0)) or 3.0)
    def _task_name(self) -> str:
        return f"orch22_wallet_{self.name}"
    def _compute_assets_value(self, assets: Dict[str, float], mkt: Orch22MarketState) -> float:
        quote = str(getattr(self.cfg, "quote", "IRT") or "IRT").upper()
        total = 0.0
        for ccy, amt in (assets or {}).items():
            c = str(ccy or "").upper().strip()
            if not c or c in (quote, "IRR", "TMN", "TOMAN", "TOMANS"):
                continue
            sym = _canon_symbol(f"{c}{quote}")
            row = (mkt.by_symbol or {}).get(sym) or {}
            px = _safe_float(row.get("close") or row.get("last") or row.get("price") or row.get("last_price") or 0.0)
            if px > 0 and amt:
                total += float(amt) * float(px)
        return float(total)
    def _count_open_orders(self, payload: Any) -> int:
        try:
            if "OrderJournal" in globals():
                orders = OrderJournal._extract_orders(payload)
                n = 0
                for o in orders or []:
                    st = OrderJournal._order_status(o)
                    if not OrderJournal._is_terminal_status(st):
                        n += 1
                return int(n)
        except Exception:
            pass
        try:
            items = []
            if isinstance(payload, list):
                items = [x for x in payload if isinstance(x, dict)]
            elif isinstance(payload, dict):
                v = payload.get("orders") or payload.get("data") or payload.get("result") or payload.get("items") or []
                if isinstance(v, list):
                    items = [x for x in v if isinstance(x, dict)]
            n = 0
            for o in items:
                st = str(o.get("status") or o.get("state") or "").lower()
                if st in ("filled", "canceled", "cancelled", "rejected", "done", "closed"):
                    continue
                n += 1
            return int(n)
        except Exception:
            return 0
    async def _run(self) -> None:
        backoff = 0.5
        for _omega_guard in range(150000):
            t0 = time.time()
            try:
                try:
                    _wdu = float(getattr(self, "_balance_disabled_until", 0.0) or 0.0)
                except Exception:
                    _wdu = 0.0
                if _wdu > time.time():
                    try:
                        self.state.last_ok = False
                        self.state.last_err = "BALANCE_COOLDOWN"
                        self.state.last_ts = float(t0)
                        self.state.reason = "BALANCE_COOLDOWN"
                    except Exception:
                        pass
                    try:
                        print(
                            f"ISOCHK_COOLDOWN phase=orch22_wallet wallet={getattr(self, 'name', '?')} until={int(_wdu)} fail_count={int(getattr(self, '_balance_fail_count', 0) or 0)}",
                            flush=True,
                        )
                    except Exception:
                        pass
                    try:
                        await asyncio.wait_for(self._stop.wait(), timeout=min(10.0, max(0.25, _wdu - time.time())))
                    except asyncio.TimeoutError:
                        pass
                    continue

                bal = await self.client.get_balance()
                cash_free, cash_total, assets_free, assets_total, ok = _parse_wallet_balance_response_v2(
                    bal, quote=str(getattr(self.cfg, "quote", "IRT") or "IRT")
                )
                if not ok: raise TradingHalt("BALANCE_FETCH_FAILED: PARSE_OK_FALSE")
                orders_payload = await self.client.list_orders(status="open", limit=200, offset=0)
                open_orders = self._count_open_orders(orders_payload)
                mkt = Orch22Orchestrator.shared_market_state()
                assets_val = self._compute_assets_value(dict(assets_total or {}), mkt)
                cash_val = float(cash_total or cash_free or 0.0)
                eq = cash_val + assets_val
                self.state.equity_irt = float(eq)
                self.state.cash_irt = float(cash_val)
                self.state.assets_irt = float(assets_val)
                self.state.open_orders = int(open_orders)
                self.state.last_ok = bool(ok)
                self.state.last_ts = float(t0)
                self.state.last_err = ""
                self.state.mode = "Hold"
                self.state.reason = ""
                self._fresh.touch()
                backoff = 0.5
            except asyncio.CancelledError:
                raise
            except (TradingHalt, Exception) as e:
                try:
                    _fc = int(getattr(self, "_balance_fail_count", 0) or 0) + 1
                    setattr(self, "_balance_fail_count", _fc)
                    setattr(self, "_balance_disabled_until", time.time() + 120.0)
                except Exception:
                    _fc = int(getattr(self, "_balance_fail_count", 0) or 0)

                self.state.last_ok = False
                self.state.last_err = str(e)[:200]
                self.state.last_ts = float(t0)
                self.state.reason = "API_FAIL"

                try:
                    print(
                        f"ISOCHK phase=orch22_wallet wallet={getattr(self, 'name', '?')} err={type(e).__name__}:{e} fail_count={_fc}",
                        flush=True,
                    )
                except Exception:
                    pass

                try:
                    _orch22_log(
                        self._log,
                        logging.WARNING,
                        "WALLET_ISOLATED",
                        wallet=self.name,
                        err=str(e)[:200],
                        fail_count=_fc,
                        cooldown_sec=120,
                    )
                except Exception:
                    pass

                try:
                    _orch22_log(self._log, logging.WARNING, "WALLET_FAIL", wallet=self.name, err=str(e)[:200])
                except Exception:
                    pass

                backoff = min(120.0, max(10.0, backoff * 1.6))
            dt = time.time() - t0
            base = max(0.10, float(self.balance_refresh_sec) - dt)
            if backoff > 0.5:
                base = max(base, backoff)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=base)
            except asyncio.TimeoutError:
                pass