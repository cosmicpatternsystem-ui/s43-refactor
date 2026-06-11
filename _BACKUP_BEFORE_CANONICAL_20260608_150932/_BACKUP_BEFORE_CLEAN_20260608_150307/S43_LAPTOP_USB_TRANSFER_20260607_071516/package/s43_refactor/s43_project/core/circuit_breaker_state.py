from .circuit_breaker import CircuitBreaker

class CircuitBreakerState(enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"