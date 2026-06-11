from .orch22_market_state import Orch22MarketState
from .orch22_system_state import Orch22SystemState
from .orch22_wallet_engine import Orch22WalletEngine
from .logger import Logger
from .shared_async_rate_limiter import SharedAsyncRateLimiter
from .exchange_client import ExchangeClient
from .orch22_market_radar import Orch22MarketRadar
from .circuit_breaker import CircuitBreaker
from .bot_config import BotConfig
from .async_rate_limiter import AsyncRateLimiter

class Orch22Orchestrator:
    _market_state: Orch22MarketState = Orch22MarketState()
    @classmethod
    def shared_market_state(cls) -> Orch22MarketState:
        return cls._market_state
    @classmethod
    def update_market_state(cls, st: Orch22MarketState) -> None:
        cls._market_state = st
    def __init__(self, cfg: "BotConfig", log: logging.Logger, *, wallet_slots: Optional[List[int]] = None,
                 stale_warn_sec: Optional[float] = None, stale_crit_sec: Optional[float] = None,
                 cancel_all_on_stale: bool = False, heartbeat_sec: Optional[float] = None) -> None:
        self.cfg = cfg
        self._log = log
        self._stop = asyncio.Event()
        self.stale_warn_sec = float(stale_warn_sec if stale_warn_sec is not None else _env_float("ORCH22_STALE_WARN_SEC", 120.0))
        self.stale_crit_sec = float(stale_crit_sec if stale_crit_sec is not None else _env_float("ORCH22_STALE_CRIT_SEC", 240.0))
        self.cancel_all_on_stale = bool(cancel_all_on_stale or _env_bool("ORCH22_CANCEL_ALL_ON_STALE", False))
        self.heartbeat_sec = float(heartbeat_sec if heartbeat_sec is not None else _env_float("ORCH22_HEARTBEAT_SEC", 5.0))
        limiter = SharedAsyncRateLimiter(cfg.rate_limit_per_min)
        breaker = CircuitBreaker(cfg.circuit_breaker_errors, cfg.circuit_breaker_cooldown_sec, log)
        self.public = ExchangeClient(cfg, token="", limiter=limiter, logger=log, breaker=breaker)
        self.radar = Orch22MarketRadar(public=self.public, cfg=cfg, log=log)
        slots = list(wallet_slots or getattr(cfg, "wallet_slots", []) or [])
        if not slots:
            slots = [1]
        self._wallet_slots = [int(x) for x in (slots or [])]
        self.wallets: Dict[str, Orch22WalletEngine] = {}
        for slot in slots:
            tok = get_arzplus_token(int(slot))
            wname = f"W{int(slot)}"
            cli = ExchangeClient(cfg, token=(tok or ""), limiter=limiter, logger=log, breaker=breaker)
            self.wallets[wname] = Orch22WalletEngine(name=wname, client=cli, cfg=cfg, log=log)
        self.state = Orch22SystemState.SAFE
        self.reason = ""
        self.started_ts = time.time()
        self._dash_task: Optional[asyncio.Task] = None
        self._wd_task: Optional[asyncio.Task] = None
    def stop(self) -> None:
        self._stop.set()
        self.radar.stop()
        for w in self.wallets.values():
            w.stop()
    async def _watchdog_loop(self) -> None:
        stage = 0
        stale_start: Optional[float] = None
        for _omega_guard in range(150000):
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=max(1.0, float(self.heartbeat_sec)))
                break
            except asyncio.TimeoutError:
                pass
            except asyncio.CancelledError:
                raise
            except Exception:
                continue
            try:
                radar_age = float(self.radar.age())
            except Exception:
                radar_age = 0.0
            worst_wallet_age = 0.0
            try:
                for w in (self.wallets or {}).values():
                    try:
                        worst_wallet_age = max(worst_wallet_age, float(w.age()))
                    except Exception:
                        continue
            except Exception:
                worst_wallet_age = worst_wallet_age
            worst = max(float(radar_age), float(worst_wallet_age))
            warn = float(self.stale_warn_sec)
            crit = float(self.stale_crit_sec)
            if worst < warn:
                stale_start = None
                stage = 0
                continue
            if stale_start is None:
                stale_start = float(time.time())
            elapsed = float(time.time() - stale_start)
            if stage < 1 and elapsed >= warn:
                try:
                    _orch22_log(self._log, logging.WARNING, "WD_TASK_RESET", worst_age=worst, elapsed=elapsed)
                except Exception:
                    pass
                try:
                    await self._task_reset()
                except Exception:
                    pass
                stage = 1
                continue
            if stage < 2 and elapsed >= crit:
                try:
                    _orch22_log(self._log, logging.ERROR, "WD_HARD_RESET", worst_age=worst, elapsed=elapsed)
                except Exception:
                    pass
                try:
                    await self._hard_reset()
                except Exception:
                    pass
                stage = 2
                continue
            if stage >= 2 and elapsed >= (crit + max(30.0, warn)):
                try:
                    _orch22_log(self._log, logging.CRITICAL, "WD_EXECV", worst_age=worst, elapsed=elapsed)
                except Exception:
                    pass
                try:
                    os.execv(sys.executable, [sys.executable] + list(sys.argv))
                except Exception:
                    pass
    async def _task_reset(self) -> None:
        try:
            if float(self.radar.age()) >= float(self.stale_warn_sec):
                old = self.radar
                try:
                    old.stop()
                except Exception:
                    pass
                try:
                    t = getattr(old, "_task", None)
                    if isinstance(t, asyncio.Task) and (not t.done()):
                        t.cancel()
                        with contextlib.suppress(Exception):
                            await t
                except Exception:
                    pass
                self.radar = Orch22MarketRadar(public=self.public, cfg=self.cfg, log=self._log)
                await self.radar.start()
        except Exception:
            pass
        for wname, w in list((self.wallets or {}).items()):
            try:
                if float(w.age()) < float(self.stale_warn_sec):
                    continue
            except Exception:
                continue
            try:
                old = w
                try:
                    old.stop()
                except Exception:
                    pass
                try:
                    t = getattr(old, "_task", None)
                    if isinstance(t, asyncio.Task) and (not t.done()):
                        t.cancel()
                        with contextlib.suppress(Exception):
                            await t
                except Exception:
                    pass
                self.wallets[wname] = Orch22WalletEngine(name=wname, client=old.client, cfg=self.cfg, log=self._log)
                await self.wallets[wname].start()
            except Exception:
                continue
    async def _hard_reset(self) -> None:
        with contextlib.suppress(Exception):
            await self._cancel_all_fail_safe()
        with contextlib.suppress(Exception):
            self.radar.stop()
        for w in (self.wallets or {}).values():
            with contextlib.suppress(Exception):
                w.stop()
        limiter = SharedAsyncRateLimiter(self.cfg.rate_limit_per_min)
        breaker = CircuitBreaker(self.cfg.circuit_breaker_errors, self.cfg.circuit_breaker_cooldown_sec, self._log)
        self.public = ExchangeClient(self.cfg, token="", limiter=limiter, logger=self._log, breaker=breaker)
        self.radar = Orch22MarketRadar(public=self.public, cfg=self.cfg, log=self._log)
        slots = list(getattr(self, "_wallet_slots", []) or [])
        if not slots:
            slots = [1]
        self.wallets = {}
        for slot in slots:
            tok = get_arzplus_token(int(slot))
            wname = f"W{int(slot)}"
            cli = ExchangeClient(self.cfg, token=(tok or ""), limiter=limiter, logger=self._log, breaker=breaker)
            self.wallets[wname] = Orch22WalletEngine(name=wname, client=cli, cfg=self.cfg, log=self._log)
        with contextlib.suppress(Exception):
            await self.radar.start()
        for w in (self.wallets or {}).values():
            with contextlib.suppress(Exception):
                await w.start()
    async def _cancel_all_fail_safe(self) -> None:
        if not self.cancel_all_on_stale:
            return
        for wname, w in self.wallets.items():
            try:
                resp = await w.client.cancel_all_orders(symbol=None)
                ok = int(_safe_float(resp.get("canceled") or resp.get("ok_count") or 0.0) or 0)
                fail = int(_safe_float(resp.get("failed") or resp.get("fail") or 0.0) or 0)
                if resp.get("ok") is False and ok == 0 and fail == 0:
                    if str(resp.get("status") or "").lower() == "ok":
                        ok = max(ok, 1)
                w.state.canceled_ok += int(ok)
                w.state.canceled_fail += int(fail)
                if ok or fail:
                    w.state.reason = "CXL_ALL"
                _orch22_log(self._log, logging.WARNING, "CANCEL_ALL", wallet=wname, ok=ok, fail=fail, hint=str(resp)[:180])
            except Exception as e:
                _orch22_log(self._log, logging.WARNING, "CANCEL_ALL_FAIL", wallet=wname, err=str(e)[:200])
    def _compute_system_state(self) -> Tuple[Orch22SystemState, str]:
        radar_age = self.radar.age()
        if self._stop.is_set():
            return Orch22SystemState.SHUTDOWN, "STOP"
        if radar_age >= float(self.stale_crit_sec):
            return Orch22SystemState.HOLD, "MKT_STALE_CRIT"
        if radar_age >= float(self.stale_warn_sec):
            return Orch22SystemState.DEGRADED, "MKT_STALE_WARN"
        return Orch22SystemState.SAFE, "OK"
    async def _dashboard_loop(self) -> None:
        for _omega_guard in range(150000):
            try:
                st = self.radar.state
                Orch22Orchestrator.update_market_state(st)
                radar_age = self.radar.age()
                focus = st.focus[:9] if st.focus else []
                top8 = st.top8[:8] if st.top8 else []
                phoenix = self.radar.phoenix_top(8)
                wsum: List[Dict[str, Any]] = []
                for w in self.wallets.values():
                    ws = w.state
                    wsum.append({
                        "w": ws.name,
                        "eq": round(ws.equity_irt, 3),
                        "ca": round(ws.cash_irt, 3),
                        "av": round(ws.assets_irt, 3),
                        "ord": int(ws.open_orders),
                        "ok": bool(ws.last_ok),
                        "age": round(w.age(), 3),
                        "mode": ws.mode,
                        "why": (ws.reason or ws.last_err or "")[:120],
                    })
                focus_sym = focus[0] if focus else ""
                rsi = self.radar.rsi(focus_sym) if focus_sym else None
                edge_bps = None
                if focus_sym:
                    row0 = (st.by_symbol or {}).get(_canon_symbol(focus_sym)) or {}
                    bid = _safe_float(row0.get("bid") or row0.get("best_bid") or row0.get("buy") or row0.get("buy_price") or 0.0)
                    ask = _safe_float(row0.get("ask") or row0.get("best_ask") or row0.get("sell") or row0.get("sell_price") or 0.0)
                    mid = (bid + ask) / 2.0 if bid > 0 and ask > 0 else 0.0
                    if mid > 0 and ask >= bid > 0:
                        edge_bps = round(((ask - bid) / mid) * 10000.0, 2)
                _orch22_log(
                    self._log,
                    logging.INFO,
                    "HEARTBEAT",
                    state=self.state.value,
                    reason=self.reason,
                    up=round(time.time() - self.started_ts, 3),
                    radar_age=round(radar_age, 3),
                    focus=focus,
                    top8=top8,
                    phoenix=phoenix,
                    rsi=(None if rsi is None else round(float(rsi), 2)),
                    edge_bps=edge_bps,
                    wallets=wsum,
                )
            except asyncio.CancelledError:
                raise
            except Exception as e:
                _orch22_log(self._log, logging.WARNING, "DASH_FAIL", err=str(e)[:200])
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=float(self.heartbeat_sec))
            except asyncio.TimeoutError:
                pass
    async def run(self) -> None:
        await self.radar.start()
        for w in self.wallets.values():
            await w.start()
        self._dash_task = asyncio.create_task(self._dashboard_loop(), name="orch22_dashboard")
        self._wd_task = asyncio.create_task(self._watchdog_loop(), name="orch22_watchdog")
        for _omega_guard in range(150000):
            try:
                st, why = self._compute_system_state()
                if st != self.state or why != self.reason:
                    self.state = st
                    self.reason = why
                    _orch22_log(self._log, logging.INFO, "STATE", state=self.state.value, reason=self.reason)
                if self.state in (Orch22SystemState.HOLD, Orch22SystemState.DEGRADED) and self.cancel_all_on_stale:
                    await self._cancel_all_fail_safe()
                await asyncio.wait_for(self._stop.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                raise
            except Exception as e:
                _orch22_log(self._log, logging.ERROR, "ORCH_FAIL", err=str(e)[:200])
                self.state = Orch22SystemState.HOLD
                self.reason = "ORCH_FAIL"
                await self._cancel_all_fail_safe()
                await asyncio.sleep(1.0)
        if self._dash_task:
            self._dash_task.cancel()
            with contextlib.suppress(Exception):
                await self._dash_task
        if self._wd_task:
            self._wd_task.cancel()
            with contextlib.suppress(Exception):
                await self._wd_task