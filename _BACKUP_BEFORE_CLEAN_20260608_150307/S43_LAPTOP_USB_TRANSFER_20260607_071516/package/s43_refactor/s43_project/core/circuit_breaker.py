from .logger import Logger

class CircuitBreaker:
    def __init__(self, max_errors: int, cooldown_sec: float, logger: logging.Logger):
        self.max_errors = int(max_errors)
        self.cooldown_sec = float(cooldown_sec)
        self._logger = logger
        self._errors = 0
        self._open_until = 0.0
    def is_open(self) -> bool:
        return time.time() < self._open_until
    def remaining_sec(self) -> float:
        try:
            return max(0.0, float(self._open_until) - time.time())
        except Exception:
            return 0.0
    def record_success(self) -> None:
        self._errors = 0
    def record_failure(self, exc: Exception) -> None:
        self._errors += 1
        if self._errors >= self.max_errors:
            self._open_until = time.time() + self.cooldown_sec
            self._logger.critical("Circuit breaker OPEN for %.0fs (err=%d): %s", self.cooldown_sec, self._errors, exc)