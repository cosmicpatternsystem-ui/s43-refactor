class PriceHistory:
    symbol: str
    timestamps: Deque[float] = field(default_factory=lambda: __import__("collections").deque(maxlen=200))
    opens: Deque[float] = field(default_factory=lambda: __import__("collections").deque(maxlen=200))
    highs: Deque[float] = field(default_factory=lambda: __import__("collections").deque(maxlen=200))
    lows: Deque[float] = field(default_factory=lambda: __import__("collections").deque(maxlen=200))
    closes: Deque[float] = field(default_factory=lambda: __import__("collections").deque(maxlen=200))
    volumes: Deque[float] = field(default_factory=lambda: __import__("collections").deque(maxlen=200))
    last_update: float = 0.0