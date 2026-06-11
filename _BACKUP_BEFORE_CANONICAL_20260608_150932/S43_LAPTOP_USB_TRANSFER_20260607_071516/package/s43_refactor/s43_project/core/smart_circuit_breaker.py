from .retry_config import RetryConfig
from .__noop_lock import _NoopLock
from .circuit_breaker import CircuitBreaker
from .circuit_breaker_state import CircuitBreakerState

class SmartCircuitBreaker:
    def __init__(self, name: str, config: RetryConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.success_count = 0
        self._lock = _NoopLock()
        self._state_change_time = time.time()
    def record_success(self):
        with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= 3:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self._state_change_time = time.time()
                    logging.info(f"Circuit breaker {self.name} closed")
            elif self.state == CircuitBreakerState.CLOSED:
                if self.failure_count > 0:
                    elapsed = time.time() - self.last_failure_time
                    if elapsed > 30:
                        self.failure_count = max(0, self.failure_count - 1)
    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            self.success_count = 0
            if (self.state == CircuitBreakerState.CLOSED and
                self.failure_count >= self.config.circuit_breaker_threshold):
                self.state = CircuitBreakerState.OPEN
                self._state_change_time = time.time()
                logging.warning(f"Circuit breaker {self.name} opened")
                self._schedule_half_open()
            elif self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
                self._state_change_time = time.time()
                logging.warning(f"Circuit breaker {self.name} re-opened")
                self._schedule_half_open()
    def _schedule_half_open(self):
        async def _transition():
            try:
                await asyncio.sleep(float(self.config.circuit_breaker_timeout))
                with self._lock:
                    if self.state == CircuitBreakerState.OPEN:
                        self.state = CircuitBreakerState.HALF_OPEN
                        self._state_change_time = time.time()
                        logging.info("event=CB_HALF_OPEN name=%s", str(self.name))
            except asyncio.CancelledError:
                raise
            except Exception:
                logging.exception("event=CB_HALF_OPEN_ERR name=%s", str(self.name))
        try:
            asyncio.create_task(_transition(), name=f"cb_halfopen_{self.name}")
        except Exception:
            logging.exception("event=CB_SCHED_ERR name=%s", str(self.name))
    def can_execute(self) -> bool:
        with self._lock:
            return self.state != CircuitBreakerState.OPEN
    def get_state(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure": self.last_failure_time,
                "state_since": self._state_change_time
            }