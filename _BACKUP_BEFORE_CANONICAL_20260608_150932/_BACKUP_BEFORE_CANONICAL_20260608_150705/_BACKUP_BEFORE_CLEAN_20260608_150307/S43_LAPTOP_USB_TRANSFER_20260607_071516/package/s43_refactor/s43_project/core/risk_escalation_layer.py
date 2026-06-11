from .risk_decision import RiskDecision
from .__noop_lock import _NoopLock

class RiskEscalationLayer:
    def __init__(
        self,
        *,
        weights: Optional[Dict[str, float]] = None,
        thresholds: Optional[List[float]] = None,
        micro_mult: float = 0.15,
        cooldown_sec: float = 30.0,
    ):
        w = dict(weights or {})
        if not w:
            w = {
                "health": float(_env_float("RISK_W_HEALTH", 1.20)),
                "soft_blacklist": float(_env_float("RISK_W_SOFT_BLACKLIST", 1.80)),
                "net_pause": float(_env_float("RISK_W_NET_PAUSE", 2.20)),
                "snapshot": float(_env_float("RISK_W_SNAPSHOT", 0.90)),
            }
        self.weights = {k: float(max(0.0, v)) for k, v in (w or {}).items()}
        if thresholds is None:
            thresholds = [
                float(_env_float("RISK_T_L0", 0.12)),
                float(_env_float("RISK_T_L1", 0.25)),
                float(_env_float("RISK_T_L2", 0.45)),
                float(_env_float("RISK_T_L3", 0.65)),
                float(_env_float("RISK_T_L4", 0.85)),
            ]
        th = [float(clamp(x, 0.0, 1.0)) for x in thresholds]
        for i in range(1, len(th)):
            if th[i] < th[i - 1]:
                th[i] = th[i - 1]
        self.thresholds = th
        self.micro_mult = float(clamp(float(micro_mult), 0.01, 0.5))
        self.cooldown_sec = float(clamp(float(cooldown_sec), 5.0, 600.0))
        self._cooldown: Dict[str, float] = {}
        self._lock = _NoopLock()
    def _key(self, wallet: str, sym: str) -> str:
        return _wallet_sym_key(wallet, sym)
    def assess(self, wallet: str, sym: str, component_scores: Dict[str, float], now: Optional[float] = None) -> RiskDecision:
        now = float(now if now is not None else time.time())
        sym = _canon_symbol(sym)
        key = self._key(wallet, sym)
        s = 0.0
        reasons: Dict[str, float] = {}
        try:
            for k, v in (component_scores or {}).items():
                if v is None:
                    continue
                sv = float(clamp(float(v), 0.0, 1.0))
                w = float(self.weights.get(str(k), 0.0) or 0.0)
                if w <= 0.0 or sv <= 0.0:
                    continue
                s += w * sv
                reasons[str(k)] = sv
        except Exception:
            pass
        composite = float(1.0 - math.exp(-float(max(0.0, s))))
        composite = float(clamp(composite, 0.0, 1.0))
        level = 5
        for i, t in enumerate(self.thresholds):
            if composite <= float(t):
                level = i
                break
        cooldown_until = 0.0
        with self._lock:
            cu = float(self._cooldown.get(key, 0.0) or 0.0)
            if cu > now:
                level = 5
                cooldown_until = cu
            elif level >= 5:
                cooldown_until = float(now + float(self.cooldown_sec))
                self._cooldown[key] = cooldown_until
            else:
                if key in self._cooldown:
                    self._cooldown.pop(key, None)
        if level <= 0:
            mult = 1.0
            allow_entries = True
        elif level == 1:
            mult = 0.8
            allow_entries = True
        elif level == 2:
            mult = 0.5
            allow_entries = True
        elif level == 3:
            mult = float(self.micro_mult)
            allow_entries = True
        elif level == 4:
            mult = float(self.micro_mult)
            allow_entries = False
        else:
            mult = 0.0
            allow_entries = False
        return RiskDecision(
            level=int(level),
            composite=float(composite),
            size_mult=float(clamp(mult, 0.0, 1.0)),
            allow_entries=bool(allow_entries),
            allow_exits=True,
            reasons=reasons,
            cooldown_until=float(cooldown_until or 0.0),
        )