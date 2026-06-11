from .clock_arbiter import ClockArbiter

class SovereignEngine:
    def __init__(self, *, max_dd: float = 0.04, win_rate: float = 0.58, risk_reward: float = 1.6,
                 max_lag_sec: float = 20.0):
        self.governor = self.SystemGovernor()
        self.risk = self.RiskSentinel(max_dd=max_dd, win_rate=win_rate, risk_reward=risk_reward)
        self.evolution = self.EvolutionaryCore()
        self.monitor = self.InvariantMonitor(max_lag_sec=max_lag_sec)
        self.stability = self.StabilityEngine()
    class SystemGovernor:
        def validate(self) -> None:
            if os.environ.get("ARZPLUS_LIVE_ARMED") != "YES":
                raise RuntimeError("ALERT SECURITY_BREACH: LIVE_MODE_NOT_ARMED")
    class RiskSentinel:
        def __init__(self, *, max_dd: float = 0.04, win_rate: float = 0.60, risk_reward: float = 1.5):
            self.max_dd = float(max_dd)
            self.peak = 0.0
            self.win_rate = float(win_rate)
            self.risk_reward = float(risk_reward)
            self._panic_mode = False
            self._last_crash_ts = 0.0
        def _kelly_fraction(self) -> float:
            p = self.win_rate
            b = self.risk_reward
            q = 1.0 - p
            frac = (p * b - q) / b
            return max(0.0, frac * 0.5)
        def kelly_cash(self, balance_cash: float) -> float:
            return float(balance_cash) * self._kelly_fraction()
        def calculate_kelly_size(self, balance_cash: float, price: Optional[float] = None) -> float:
            bal = float(balance_cash or 0.0)
            if bal <= 0:
                return 0.0
            win_rate = float(self.win_rate)
            risk_reward = float(self.risk_reward)
            q = 1.0 - win_rate
            kelly_f = (risk_reward * win_rate - q) / risk_reward
            safe_f = max(0.0, float(kelly_f) * 0.5)
            cash_budget = bal * safe_f
            if price is None:
                return float(cash_budget)
            px = float(price or 0.0)
            if px <= 0:
                return 0.0
            return max(0.0, float(cash_budget) / px)
        def get_kelly_qty(self, balance_cash: float, price: float) -> float:
            return float(self.calculate_kelly_size(float(balance_cash), price=float(price)))
        def is_safe(self, balance_cash: float) -> bool:
            bal = float(balance_cash)
            if bal > self.peak:
                self.peak = bal
            return bal >= self.peak * (1.0 - self.max_dd)
        def arm_panic_if_flash_crash(self, prices: "Deque[float]", *, lookback: int = 10, drop_thr: float = -0.03) -> None:
            try:
                if prices is None or len(prices) < max(3, int(lookback)):
                    return
                p0 = float(prices[-int(lookback)])
                p1 = float(prices[-1])
                if p0 > 0:
                    change = (p1 - p0) / p0
                    if change <= float(drop_thr):
                        self._panic_mode = True
                        self._last_crash_ts = float(time.time())
            except Exception:
                return
        def panic_sniper_active(self, *, window_sec: int = 300) -> bool:
            if not self._panic_mode:
                return False
            if (time.time() - float(self._last_crash_ts)) <= float(window_sec):
                return True
            self._panic_mode = False
            return False
        def build_panic_sniper_orders(
            self,
            current_price: float,
            balance_cash: float,
            *,
            profit_target: float = 0.07,
            max_balance_frac: float = 0.25,
            min_balance_frac: float = 0.05,
            buy_offsets: "Tuple[float, ...]" = (0.005, 0.012, 0.020),
            cid_prefix: str = "SOV_SNIPER"
        ) -> "List[Dict[str, float]]":
            px = float(current_price or 0.0)
            bal = float(balance_cash or 0.0)
            if px <= 0 or bal <= 0:
                return []
            kelly_cash = self.kelly_cash(bal)
            sniper_cash = min(bal * float(max_balance_frac), max(kelly_cash * 2.0, bal * float(min_balance_frac)))
            if sniper_cash <= 0:
                return []
            qty_total = sniper_cash / px
            qty_each = qty_total / max(1, len(buy_offsets))
            ts = int(time.time())
            orders: "List[Dict[str, float]]" = []
            for i, off in enumerate(buy_offsets):
                bpx = px * (1.0 - float(off))
                spx = bpx * (1.0 + float(profit_target))
                orders.append({"side": "buy", "price": float(bpx), "qty": float(qty_each), "cid": f"{cid_prefix}_B{i}_{ts}"})
                orders.append({"side": "sell", "price": float(spx), "qty": float(qty_each), "cid": f"{cid_prefix}_TP{i}_{ts}"})
            return orders
    class EvolutionaryCore:
        def __init__(self):
            self.prices: "Deque[float]" = __import__("collections").deque(maxlen=200)
            self.lookback_sigma: "Deque[float]" = __import__("collections").deque(maxlen=100)
        def update(self, price: float) -> None:
            try:
                self.prices.append(float(price))
            except Exception:
                pass
        def sigma(self) -> float:
            if len(self.prices) < 30:
                s = 0.001
            else:
                mean_px = float(np.mean(self.prices))
                if mean_px <= 0:
                    s = 0.001
                else:
                    s = float(np.std(self.prices)) / mean_px
            try:
                self.lookback_sigma.append(float(s))
            except Exception:
                pass
            return float(s)
        def calculate_damped_sigma(self, raw_sigma: float) -> float:
            try:
                rs = float(raw_sigma)
            except Exception:
                rs = 0.0
            if rs < 0:
                rs = 0.0
            return float(np.log1p(rs))
        def get_asymmetric_ladder(self, current_price: float, raw_sigma: float, *, side: str = "buy",
                                 levels: int = 5) -> "List[float]":
            px = float(current_price or 0.0)
            if px <= 0:
                return []
            sigma_d = self.calculate_damped_sigma(raw_sigma)
            crash_shield = 1.5 if float(raw_sigma or 0.0) > 0.025 else 1.0
            s = str(side).lower()
            growth_factor = 1.4 if s == "buy" else 1.7
            ladder: "List[float]" = []
            for i in range(int(levels)):
                offset = sigma_d * (float(growth_factor) ** i) * float(crash_shield)
                if s == "buy":
                    lvl = px * (1.0 - float(offset))
                else:
                    lvl = px * (1.0 + float(offset))
                ladder.append(round(float(lvl), 2))
            return ladder
        def get_exponential_ladder(
            self,
            current_price: float,
            raw_sigma: float,
            side: str = "buy",
            levels: int = 5,
        ) -> "List[float]":
            px = float(current_price or 0.0)
            if px <= 0:
                return []
            s = str(side).lower().strip()
            sigma_d = self.calculate_damped_sigma(float(raw_sigma))
            if s == "sell":
                z_scores = (0.8, 1.4, 2.2, 3.2, 4.5)
            else:
                s = "buy"
                z_scores = (1.0, 1.5, 2.2, 3.0, 4.0)
            out: "List[float]" = []
            n = min(int(levels), len(z_scores))
            for i in range(n):
                offset = float(sigma_d) * float(z_scores[i])
                if offset < 0.0:
                    offset = 0.0
                if offset > 0.95:
                    offset = 0.95
                lvl = px * (1.0 - offset) if s == "buy" else px * (1.0 + offset)
                out.append(round(float(lvl), 2))
            return out
        def compute_ladder(
            self,
            current_price: float,
            *,
            sigma: Optional[float] = None,
            side: str = "buy",
            levels: int = 5,
            growth: float = 1.6,
        ) -> "List[float]":
            raw = float(sigma) if sigma is not None else self.sigma()
            _ = float(growth)
            return list(self.get_exponential_ladder(float(current_price), raw, side=str(side), levels=int(levels)))
    class InvariantMonitor:
        def __init__(self, *, max_lag_sec: float = 20.0, volume_window: int = 60):
            self.max_lag_sec = float(max_lag_sec)
            self.volume_history: "Deque[float]" = __import__("collections").deque(maxlen=int(volume_window))
        def check_lag(self, exchange_ts_ms: float) -> "Tuple[bool, float]":
            try:
                ts = float(exchange_ts_ms)
            except Exception:
                ts = time.time() * 1000.0
            ts_s = float(ClockArbiter._epoch_to_seconds(ts))
            if ts_s <= 0.0 or (not math.isfinite(ts_s)):
                ts_s = float(time.time())
            lag = time.time() - ts_s
            return (lag <= self.max_lag_sec), float(lag)
        def update_volume(self, current_volume: Optional[float]) -> None:
            try:
                cv = float(current_volume) if current_volume is not None else 0.0
            except Exception:
                cv = 0.0
            if cv > 0.0 and cv == cv:
                try:
                    self.volume_history.append(cv)
                except Exception:
                    pass
        def detect_whale_activity(
            self,
            current_volume: float,
            volume_history: Optional[Any] = None,
            *,
            multiplier: float = 3.0,
            min_len: int = 10,
        ) -> bool:
            hist = volume_history if volume_history is not None else self.volume_history
            try:
                h = list(hist)
            except Exception:
                return False
            if len(h) < int(min_len):
                return False
            try:
                avg = float(sum(h)) / float(len(h))
            except Exception:
                return False
            try:
                cv = float(current_volume)
            except Exception:
                return False
            if cv <= 0.0 or avg <= 0.0:
                return False
            return cv > (avg * float(multiplier))
        def _volume_hist_for_symbol(self, symbol: str, *, window: int = 60) -> "Deque[float]":
            sym = _canon_symbol(symbol)
            if not hasattr(self, "_vol_hist_by_symbol"):
                self._vol_hist_by_symbol: "Dict[str, Deque[float]]" = {}
                self._whale_last_ts_by_symbol: "Dict[str, float]" = {}
            dq = self._vol_hist_by_symbol.get(sym)
            if dq is None or int(getattr(dq, "maxlen", 0) or 0) != int(window):
                dq = __import__("collections").deque(maxlen=int(window))
                self._vol_hist_by_symbol[sym] = dq
            return dq
        def detect_whale_shield(
            self,
            symbol: str,
            current_volume: float,
            *,
            multiplier: float = 3.0,
            min_len: int = 10,
            window: int = 60,
        ) -> bool:
            hist = self._volume_hist_for_symbol(symbol, window=int(window))
            try:
                cv = float(current_volume)
            except Exception:
                cv = 0.0
            if cv > 0.0 and cv == cv:
                try:
                    hist.append(cv)
                except Exception:
                    pass
            active = bool(self.detect_whale_activity(cv, hist, multiplier=float(multiplier), min_len=int(min_len)))
            if active:
                try:
                    self._whale_last_ts_by_symbol[_canon_symbol(symbol)] = time.time()
                except Exception:
                    pass
            return active
        def last_whale_ts(self, symbol: str) -> float:
            sym = _canon_symbol(symbol)
            try:
                return float(getattr(self, "_whale_last_ts_by_symbol", {}).get(sym, 0.0) or 0.0)
            except TradingHalt:
                raise
            except Exception:
                return 0.0
    class StabilityEngine:
        def refresh(self) -> None:
            try:
                gc.collect()
            except Exception:
                pass