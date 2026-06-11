from .trade_health import TradeHealth

class TradeHealthController:
    def __init__(
        self,
        market_thr_s: float = 4.0,
        book_thr_s: float = 4.0,
        skew_soft_s: float = 8.0,
        skew_degraded_s: float = 20.0,
        skew_halt_s: float = 60.0,
        *,
        skew_ewma_tau_sec: float = 15.0,
        skew_deadband_sec: float = 0.35,
        vol_ewma_tau_sec: float = 120.0,
        vol_ref_bps_per_min: float = 8.0,
        vol_sensitivity: float = 0.35,
        thr_min_mult: float = 0.30,
        thr_max_mult: float = 1.60,
    ):
        self.market_thr_s = float(market_thr_s)
        self.book_thr_s = float(book_thr_s)
        self.skew_soft_s = float(skew_soft_s)
        self.skew_degraded_s = float(skew_degraded_s)
        self.skew_halt_s = float(skew_halt_s)
        self.skew_ewma_tau_sec = float(clamp(float(skew_ewma_tau_sec), 2.0, 120.0))
        self.skew_deadband_sec = float(clamp(float(skew_deadband_sec), 0.0, 5.0))
        self.vol_ewma_tau_sec = float(clamp(float(vol_ewma_tau_sec), 10.0, 1800.0))
        self.vol_ref_bps_per_min = float(max(1e-6, float(vol_ref_bps_per_min)))
        self.vol_sensitivity = float(clamp(float(vol_sensitivity), 0.0, 2.0))
        self.thr_min_mult = float(clamp(float(thr_min_mult), 0.05, 1.0))
        self.thr_max_mult = float(clamp(float(thr_max_mult), 1.0, 4.0))
        self._skew_ewma: Dict[str, float] = {}
        self._skew_ts: Dict[str, float] = {}
        self._last_mid: Dict[str, float] = {}
        self._last_mid_ts: Dict[str, float] = {}
        self._vol_ewma_bps_min: Dict[str, float] = {}
        self._halt_since: Dict[str, float] = {}
    def _time_alpha(self, dt: float, tau: float) -> float:
        dt = float(max(0.0, dt))
        tau = float(max(1e-6, tau))
        try:
            return float(1.0 - math.exp(-dt / tau))
        except Exception:
            return 0.0
    def _update_skew(self, sym: str, skew: float, now: float) -> float:
        sym = _canon_symbol(sym)
        prev = float(self._skew_ewma.get(sym, float(skew)))
        pts = float(self._skew_ts.get(sym, now))
        a = self._time_alpha(now - pts, float(self.skew_ewma_tau_sec))
        ew = (1.0 - a) * prev + a * float(skew)
        if abs(float(skew) - float(ew)) < float(self.skew_deadband_sec):
            out = float(ew)
        else:
            out = float(skew)
            ew = float((1.0 - a) * ew + a * float(skew))
        self._skew_ewma[sym] = float(ew)
        self._skew_ts[sym] = float(now)
        return float(max(0.0, out))
    def _update_vol(self, sym: str, mid: float, now: float) -> float:
        sym = _canon_symbol(sym)
        mid = float(mid)
        if not math.isfinite(mid) or mid <= 0.0:
            return float(self._vol_ewma_bps_min.get(sym, 0.0) or 0.0)
        lm = float(self._last_mid.get(sym, mid))
        lts = float(self._last_mid_ts.get(sym, now))
        dt = float(max(0.0, now - lts))
        inst = 0.0
        try:
            if dt >= 0.2 and lm > 0.0 and math.isfinite(lm) and lm != mid:
                bps = abs(math.log(mid / lm)) * 10000.0
                inst = float(bps) * (60.0 / dt)
        except Exception:
            inst = 0.0
        prev = float(self._vol_ewma_bps_min.get(sym, inst))
        a = self._time_alpha(dt, float(self.vol_ewma_tau_sec))
        ew = (1.0 - a) * prev + a * float(inst)
        self._vol_ewma_bps_min[sym] = float(max(0.0, ew))
        self._last_mid[sym] = float(mid)
        self._last_mid_ts[sym] = float(now)
        return float(max(0.0, ew))
    def _dyn_thr(self, base: float, vol_bps_min: float) -> float:
        base = float(max(0.25, base))
        vn = float(max(0.0, vol_bps_min)) / float(self.vol_ref_bps_per_min)
        mult = float(1.0 / (1.0 + float(self.vol_sensitivity) * float(vn)))
        mult = float(clamp(mult, float(self.thr_min_mult), float(self.thr_max_mult)))
        return float(base * mult)
    def evaluate(
        self,
        sym: str,
        mkt_age_s: Optional[float],
        book_age_s: Optional[float],
        skew_s: Optional[float],
        *,
        mid: Optional[float] = None,
        now_ts: Optional[float] = None,
        grace_mult: float = 1.0,
    ) -> TradeHealth:
        now = float(now_ts if now_ts is not None else time.time())
        symc = _canon_symbol(sym)
        m = float(mkt_age_s) if mkt_age_s is not None else float("inf")
        b = float(book_age_s) if book_age_s is not None else float("inf")
        k = float(skew_s) if skew_s is not None else float("inf")
        if not math.isfinite(m):
            m = float("inf")
        if not math.isfinite(b):
            b = float("inf")
        if not math.isfinite(k):
            k = float("inf")
        vol = 0.0
        try:
            if mid is not None:
                vol = self._update_vol(symc, float(mid), now)
        except Exception:
            vol = float(self._vol_ewma_bps_min.get(symc, 0.0) or 0.0)
        m_thr = self._dyn_thr(float(self.market_thr_s), float(vol))
        b_thr = self._dyn_thr(float(self.book_thr_s), float(vol))
        gm = 1.0
        try:
            gm = float(grace_mult or 1.0)
        except Exception:
            gm = 1.0
        try:
            gm_max = float(_env_float("HEALTH_WD_GRACE_MAX_MULT", 1.25) or 1.25)
        except Exception:
            gm_max = 1.25
        gm = float(clamp(gm, 1.0, float(gm_max)))
        m_thr = float(m_thr) * gm
        b_thr = float(b_thr) * gm
        k_s = k
        try:
            if math.isfinite(k):
                k_s = self._update_skew(symc, float(k), now)
        except Exception:
            k_s = k
        reasons = {
            "mkt_age": float(m),
            "book_age": float(b),
            "skew": float(k_s),
            "vol_bps_min": float(vol),
            "mkt_thr_dyn": float(m_thr),
            "book_thr_dyn": float(b_thr),
            "grace_mult": float(gm),
        }
        sev = 0.0
        if m > m_thr:
            sev += min(4.0, (m - m_thr) / max(0.5, m_thr) * 2.0)
        if b > b_thr:
            sev += min(4.0, (b - b_thr) / max(0.5, b_thr) * 2.0)
        if k_s > self.skew_soft_s:
            sev += min(4.0, (k_s - self.skew_soft_s) / max(1.0, self.skew_soft_s) * 1.5)
        sev = float(clamp(sev, 0.0, 10.0))
        try:
            halt_cooldown = float(os.getenv("HALT_COOLDOWN_SEC", "60.0") or 60.0)
        except Exception:
            halt_cooldown = 60.0
        halt_cooldown = float(max(10.0, min(600.0, halt_cooldown)))
        severe_halt = (k_s >= self.skew_halt_s) or (m >= m_thr * 6.0) or (b >= b_thr * 6.0)
        if severe_halt:
            hs = float(self._halt_since.get(symc, 0.0) or 0.0)
            if hs <= 0.0:
                self._halt_since[symc] = float(now)
                return TradeHealth("HALT", 0.0, sev, reasons)
            if (now - hs) >= halt_cooldown:
                return TradeHealth("DEGRADED", 0.45, sev, reasons)
            return TradeHealth("HALT", 0.0, sev, reasons)
        self._halt_since[symc] = 0.0
        if (k_s >= self.skew_degraded_s) or (m >= m_thr * 2.5) or (b >= b_thr * 2.5):
            return TradeHealth("DEGRADED", 0.45, sev, reasons)
        if (k_s >= self.skew_soft_s) or (m >= m_thr) or (b >= b_thr):
            return TradeHealth("SOFT", 0.75, sev, reasons)
        return TradeHealth("NORMAL", 1.0, sev, reasons)