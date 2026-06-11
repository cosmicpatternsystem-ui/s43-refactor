from .sovereign_engine import SovereignEngine

class SovereignCore:
    def __init__(self, balance_provider, order_executor, *, max_dd: float = 0.04,
                 win_rate: float = 0.58, risk_reward: float = 1.6, max_lag_sec: float = 25.0):
        self.engine = SovereignEngine(max_dd=max_dd, win_rate=win_rate, risk_reward=risk_reward, max_lag_sec=max_lag_sec)
        self.bp = balance_provider
        self.exec = order_executor
        self._px_hist: "Deque[float]" = __import__("collections").deque(maxlen=120)
        self._sniper_fired_ts: float = 0.0
        self.warmup_done: bool = False
    async def _safe_cancel_all(self) -> None:
        for name in ("cancel_all", "cancel_all_orders", "cancel_all_open_orders"):
            fn = getattr(self.exec, name, None)
            if fn and callable(fn):
                try:
                    await fn()
                except Exception:
                    pass
                return
    async def _place(self, side: str, price: float, qty: float, cid: str = "") -> None:
        fn = getattr(self.exec, "place_order", None)
        if not fn or not callable(fn):
            raise RuntimeError("order_executor has no place_order()")
        try:
            try:
                try:
                    import inspect
                except:
                    pass
            except:
                pass
            sig = inspect.signature(fn)
            n = len(sig.parameters)
        except Exception:
            n = 4
        try:
            if n <= 2:
                await fn(float(price), float(qty))
            elif n == 3:
                await fn(str(side), float(price), float(qty))
            else:
                await fn(str(side), float(price), float(qty), str(cid))
        except TypeError:
            try:
                await fn(float(price), float(qty))
            except Exception:
                await fn(str(side), float(price), float(qty), str(cid))
    async def execute_sovereign_strategy(
        self,
        current_price: float,
        ts_ms: float,
        sigma: Optional[float] = None,
        current_volume: Optional[float] = None,
        volume_history: Optional[List[float]] = None,
        *,
        signal: str = "BUY",
    ) -> None:
        self.engine.governor.validate()
        ok, _lag = self.engine.monitor.check_lag(ts_ms)
        if not ok:
            return
        px = float(current_price or 0.0)
        if px <= 0:
            return
        if not self.warmup_done:
            for _ in range(20):
                self._px_hist.append(px)
                self.engine.evolution.update(px)
            self.warmup_done = True
        self._px_hist.append(px)
        self.engine.evolution.update(px)
        sig = float(sigma) if sigma is not None else self.engine.evolution.sigma()
        whale_active = False
        try:
            if current_volume is not None:
                whale_active = bool(self.engine.monitor.detect_whale_activity(float(current_volume), volume_history))
                self.engine.monitor.update_volume(float(current_volume))
        except Exception:
            whale_active = False
        effective_sigma = float(sig) * 2.0 if whale_active else float(sig)
        balance = float(await self.bp.get_balance())
        if not self.engine.risk.is_safe(balance):
            await self._safe_cancel_all()
            raise SystemExit("ALERT [KILL-SWITCH] Risk Threshold Exceeded.")
        self.engine.risk.arm_panic_if_flash_crash(self._px_hist)
        if self.engine.risk.panic_sniper_active():
            if (time.time() - float(self._sniper_fired_ts)) > 30:
                orders = self.engine.risk.build_panic_sniper_orders(px, balance, profit_target=0.07)
                for o in orders:
                    await self._place(o["side"], o["price"], o["qty"], o.get("cid", "SOV_SNIPER"))
                self._sniper_fired_ts = float(time.time())
            self.engine.stability.refresh()
            return
        if str(signal).upper() == "BUY":
            qty_total = float(self.engine.risk.calculate_kelly_size(balance, price=px))
            ladder = self.engine.evolution.get_exponential_ladder(px, effective_sigma, side="buy", levels=5)
            try:
                if ladder and abs(px - float(ladder[0])) / px < 0.001:
                    ladder[0] = px
            except Exception:
                pass
            if qty_total > 0 and ladder:
                qty_each = qty_total / len(ladder)
                ts = int(time.time())
                for i, lvl_px in enumerate(ladder):
                    await self._place("buy", float(lvl_px), float(qty_each), f"SOV_CID_{i}_{ts}")
        self.engine.stability.refresh()