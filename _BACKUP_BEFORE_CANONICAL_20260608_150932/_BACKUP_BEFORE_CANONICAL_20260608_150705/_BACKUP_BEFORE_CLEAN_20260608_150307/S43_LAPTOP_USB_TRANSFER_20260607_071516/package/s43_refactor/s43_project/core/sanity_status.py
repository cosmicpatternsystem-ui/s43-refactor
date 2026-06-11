class SanityStatus:
    active: bool = False
    reason: str = ""
    since_ts: float = 0.0
    until_ts: float = 0.0
    ok_streak: int = 0
    ema_mid: float = 0.0
    ema_liq: float = 0.0
    liq_hist: deque = field(default_factory=lambda: __import__("collections").deque(maxlen=20))
    debounce_hits: int = 0
    debounce_window_start_ts: float = 0.0
    soft: bool = False