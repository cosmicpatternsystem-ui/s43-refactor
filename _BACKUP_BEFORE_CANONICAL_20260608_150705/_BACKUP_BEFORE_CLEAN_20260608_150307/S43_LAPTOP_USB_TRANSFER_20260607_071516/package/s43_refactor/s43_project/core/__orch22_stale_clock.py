class _Orch22StaleClock:
    __slots__ = ("_ts",)
    def __init__(self) -> None:
        self._ts = 0.0
    def touch(self) -> None:
        try:
            self._ts = float(time.time())
        except Exception:
            self._ts = 0.0
    def age(self) -> float:
        try:
            if not self._ts:
                return 1e9
            return max(0.0, float(time.time()) - float(self._ts))
        except Exception:
            return 1e9