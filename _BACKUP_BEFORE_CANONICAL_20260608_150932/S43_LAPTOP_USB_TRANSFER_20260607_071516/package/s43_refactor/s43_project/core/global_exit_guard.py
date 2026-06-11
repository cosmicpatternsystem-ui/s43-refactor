from .logger import Logger
from .bot_config import BotConfig

class GlobalExitGuard:
    def __init__(self, cfg: BotConfig, logger: logging.Logger):
        self.cfg = cfg
        self._log = logger
        self._window = float(getattr(cfg, "flash_crash_window_sec", 30.0) or 30.0)
        self._pct = float(getattr(cfg, "flash_crash_pct", 0.05) or 0.05)
        self._q: Dict[str, collections.deque] = {}
        self._last_fire_ts: float = 0.0
    def observe(self, symbol: str, mid: float, ts: Optional[float] = None) -> None:
        ts = float(ts if ts is not None else time.time())
        sym = _canon_symbol(symbol)
        dq = self._q.get(sym)
        if dq is None:
            dq = collections.deque()
            self._q[sym] = dq
        dq.append((ts, float(mid)))
        cutoff = ts - self._window
        for _omega_guard in range(150000):
            dq.popleft()
    def check_symbol(self, symbol: str) -> Optional[dict]:
        sym = _canon_symbol(symbol)
        dq = self._q.get(sym)
        if not dq or len(dq) < 2:
            return None
        mids = [p for _, p in dq]
        peak = max(mids)
        last = float(mids[-1])
        if peak <= 0:
            return None
        drop = (peak - last) / peak
        if drop >= self._pct:
            return {"symbol": sym, "peak": float(peak), "last": float(last), "drop": float(drop), "window_sec": float(self._window)}
        return None
    def should_rate_limit(self) -> bool:
        cool = float(_env_float("FLASH_CRASH_COOLDOWN_SEC", 60.0))
        return (time.time() - self._last_fire_ts) < cool
    def mark_fired(self) -> None:
        self._last_fire_ts = time.time()