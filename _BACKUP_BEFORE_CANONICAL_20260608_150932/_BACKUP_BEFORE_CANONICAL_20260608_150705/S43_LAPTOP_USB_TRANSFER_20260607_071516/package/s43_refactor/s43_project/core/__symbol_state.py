class _SymbolState:
    last_mid: float = 0.0
    ema_fast: float = 0.0
    ema_slow: float = 0.0
    ema_var: float = 0.0
    ema_imb: float = 0.0
    ema_micro: float = 0.0
    ema_spread_bps: float = 0.0
    last_score: float = 0.0
    returns: Deque[float] = field(default_factory=lambda: __import__("collections").deque(maxlen=256))