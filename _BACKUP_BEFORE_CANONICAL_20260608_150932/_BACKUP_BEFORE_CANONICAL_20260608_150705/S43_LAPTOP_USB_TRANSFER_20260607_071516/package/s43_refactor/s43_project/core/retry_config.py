from .retry_strategy import RetryStrategy

class RetryConfig:
    strategy: RetryStrategy
    max_attempts: int
    base_delay: float
    max_delay: float
    jitter: bool = False
    backoff_factor: float = 2.0
    timeout_multiplier: float = 1.5
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0