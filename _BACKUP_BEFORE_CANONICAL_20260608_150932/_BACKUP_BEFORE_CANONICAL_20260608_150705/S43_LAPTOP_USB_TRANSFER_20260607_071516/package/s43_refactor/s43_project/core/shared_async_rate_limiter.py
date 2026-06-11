from .async_rate_limiter import AsyncRateLimiter

class SharedAsyncRateLimiter:
    def __init__(self, per_minute: int, min_interval_floor_sec: float = 1.05):
        self.per_minute = max(1, int(per_minute))
        self._base_min_interval = (60.0 / float(self.per_minute)) * 1.10
        self._min_interval = max(float(min_interval_floor_sec), float(self._base_min_interval))
        self._hold_until = 0.0
        self._lock = asyncio.Lock()
        self._last = 0.0
        self._req_times = __import__("collections").deque(maxlen=max(64, self.per_minute * 5))
        self._util_pct = 0.0
        self._hold_remain = 0.0
        self._last_sleep = 0.0
    async def wait(self) -> None:
        async with self._lock:
            now = time.time()
            sleep_for = 0.0
            if self._hold_until > now:
                sleep_for = self._hold_until - now
            dt = now - self._last
            sleep_for = max(sleep_for, self._min_interval - dt)
            if sleep_for > 0.0:
                self._last_sleep = float(sleep_for)
                await asyncio.sleep(sleep_for)
            self._last = time.time()
            try:
                now2 = float(self._last)
                self._req_times.append(now2)
                cutoff = now2 - 60.0
                for _omega_guard in range(150000):
                    self._req_times.popleft()
                self._util_pct = min(100.0, (len(self._req_times) / float(max(1, self.per_minute))) * 100.0)
                self._hold_remain = max(0.0, float(self._hold_until) - now2)
            except Exception:
                pass
    async def penalize(self, pause_sec: float, hard: bool = False) -> None:
        pause = float(max(0.0, pause_sec or 0.0))
        if pause <= 0.0 and not hard:
            return
        async with self._lock:
            now = time.time()
            if pause > 0.0:
                self._hold_until = max(self._hold_until, now + pause)
            bump = 1.25 if hard else 1.12
            self._min_interval = min(12.0, max(self._min_interval, self._min_interval * bump, 1.05))
    async def reward(self) -> None:
        async with self._lock:
            self._min_interval = max(self._base_min_interval, self._min_interval * 0.985, 1.05)
    def metrics(self) -> dict:
        try:
            return {
                "per_minute": int(getattr(self, "per_minute", 0) or 0),
                "min_interval": float(getattr(self, "_min_interval", 0.0) or 0.0),
                "base_min_interval": float(getattr(self, "_base_min_interval", 0.0) or 0.0),
                "hold_remain": float(getattr(self, "_hold_remain", 0.0) or 0.0),
                "util_pct": float(getattr(self, "_util_pct", 0.0) or 0.0),
                "last_sleep": float(getattr(self, "_last_sleep", 0.0) or 0.0),
            }
        except Exception:
            return {}