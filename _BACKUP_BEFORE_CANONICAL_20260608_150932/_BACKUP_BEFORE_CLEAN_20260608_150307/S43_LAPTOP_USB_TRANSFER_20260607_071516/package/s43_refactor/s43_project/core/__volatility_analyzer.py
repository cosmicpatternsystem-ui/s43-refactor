class _VolatilityAnalyzer:
    def __init__(self, maxlen: int = 120):
        self.maxlen = int(maxlen or 120)
        self._hist: Dict[str, Deque[float]] = {}
    def update(self, symbol: str, price: float) -> None:
        sym = _canon_symbol(symbol)
        dq = self._hist.get(sym)
        if dq is None:
            dq = __import__("collections").deque(maxlen=self.maxlen)
            self._hist[sym] = dq
        try:
            p = float(price)
        except Exception:
            return
        if p > 0:
            dq.append(p)
    def get_volatility(self, symbol: Optional[str] = None) -> float:
        sym = _canon_symbol(symbol) if symbol else (next(iter(self._hist.keys()), ""))
        dq = self._hist.get(sym) if sym else None
        if not dq or len(dq) < 20:
            return 0.001
        arr = np.array(list(dq), dtype=float)
        mu = float(arr.mean()) if arr.size else 0.0
        if mu <= 0:
            return 0.001
        sig = float(arr.std() / mu)
        return max(0.0005, min(0.05, sig))