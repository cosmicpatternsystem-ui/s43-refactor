class AsyncRateLimiter:
    def __init__(
        self,
        requests_per_minute: int,
        burst_size: int = 5,
        max_backoff_sec: float = 60.0
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.max_backoff_sec = max_backoff_sec
        self._interval = 60.0 / requests_per_minute
        self._tokens = burst_size
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()
        self._consecutive_failures = 0
        self._backoff_factor = 1.0
    async def acquire(self, weight: int = 1) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_update
            self._tokens = min(
                self.burst_size,
                self._tokens + elapsed / self._interval
            )
            self._last_update = now
            required = weight
            if self._tokens < required:
                deficit = required - self._tokens
                wait_time = deficit * self._interval
                if self._consecutive_failures > 0:
                    backoff = min(
                        self.max_backoff_sec,
                        self._backoff_factor * (2 ** self._consecutive_failures)
                    )
                    wait_time = max(wait_time, backoff)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    self._tokens = 0
                else:
                    self._tokens -= required
            else:
                self._tokens -= required
                self._consecutive_failures = 0
                self._backoff_factor = 1.0
    async def __aenter__(self):
        await self.acquire()
        return self
    async def __aexit__(self, exc_type, exc, tb):
        try:
            async with self._lock:
                if exc_type is None:
                    self._consecutive_failures = 0
                    self._backoff_factor = 1.0
                else:
                    self._consecutive_failures = min(int(self._consecutive_failures) + 1, 20)
                    msg = str(exc or "").lower()
                    bump = 1.25 if any(k in msg for k in ("429", "rate limit", "too many requests", "throttle")) else 1.10
                    self._backoff_factor = min(float(self._backoff_factor) * float(bump), float(self.max_backoff_sec or 60.0))
        except Exception:
            pass
        return False