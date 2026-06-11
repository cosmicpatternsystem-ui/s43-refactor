class SymbolSnapshot:
    symbol: str
    ts: float = 0.0
    mid: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    status: str = "MISSING"   #
    reason: str = ""
    quality: int = 0          #
    src: str = ""
    fail_count: int = 0
    last_attempt_ts: float = 0.0
    last_error: str = ""
    def age_sec(self, now: Optional[float] = None) -> float:
        try:
            now0 = float(time.time() if now is None else now)
        except Exception:
            now0 = float(time.time())
        try:
            ts0 = float(self.ts or 0.0)
            if ts0 > 1e11:
                ts0 = ts0 / 1000.0
            return float("inf") if ts0 <= 0.0 else max(0.0, float(now0) - float(ts0))
        except Exception:
            return float("inf")