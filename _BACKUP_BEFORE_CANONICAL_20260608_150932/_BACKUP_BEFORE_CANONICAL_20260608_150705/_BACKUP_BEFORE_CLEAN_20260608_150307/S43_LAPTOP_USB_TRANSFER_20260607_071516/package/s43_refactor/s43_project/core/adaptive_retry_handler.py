from .retry_strategy import RetryStrategy
from .retry_config import RetryConfig
from .smart_circuit_breaker import SmartCircuitBreaker
from .temporary_pause import TemporaryPause
from .circuit_breaker import CircuitBreaker

class AdaptiveRetryHandler:
    def __init__(self):
        self.breakers: Dict[str, SmartCircuitBreaker] = {}
        self.retry_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"success": 0, "failures": 0, "retries": 0}
        )
    def get_circuit_breaker(self, endpoint: str, config: RetryConfig) -> SmartCircuitBreaker:
        if endpoint not in self.breakers:
            self.breakers[endpoint] = SmartCircuitBreaker(endpoint, config)
        return self.breakers[endpoint]
    async def execute_with_retry(
        self,
        coro_func: Callable[..., Awaitable[Any]],
        endpoint: str,
        retry_config: RetryConfig,
        *args,
        **kwargs
    ) -> Any:
        breaker = self.get_circuit_breaker(endpoint, retry_config)
        for attempt in range(1, retry_config.max_attempts + 1):
            if not breaker.can_execute():
                raise TemporaryPause(f"Circuit breaker open for {endpoint}", pause_sec=float(breaker.config.circuit_breaker_timeout))
            try:
                timeout = retry_config.base_delay * retry_config.timeout_multiplier
                result = await asyncio.wait_for(
                    coro_func(*args, **kwargs),
                    timeout=timeout
                )
                breaker.record_success()
                self.retry_stats[endpoint]["success"] += 1
                return result
            except asyncio.TimeoutError:
                self.retry_stats[endpoint]["failures"] += 1; breaker.record_failure()
                logging.warning(
                    f"Timeout on {endpoint} (attempt {attempt}/{retry_config.max_attempts})"
                )
            except aiohttp.ClientError as e:
                self.retry_stats[endpoint]["failures"] += 1; breaker.record_failure()
                logging.warning(
                    f"Client error on {endpoint}: {e} "
                    f"(attempt {attempt}/{retry_config.max_attempts})"
                )
            except Exception as e:
                self.retry_stats[endpoint]["failures"] += 1
                breaker.record_failure()
                logging.error(
                    f"Error on {endpoint}: {e} "
                    f"(attempt {attempt}/{retry_config.max_attempts})"
                )
            if attempt < retry_config.max_attempts:
                delay = self._calculate_delay(attempt, retry_config)
                logging.info(f"Retrying {endpoint} in {delay:.2f}s")
                await asyncio.sleep(delay)
        raise TemporaryPause(f"Failed to execute {endpoint} after {retry_config.max_attempts} attempts", pause_sec=float(retry_config.base_delay))
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        if config.strategy == RetryStrategy.IMMEDIATE:
            delay = 0.1
        elif config.strategy == RetryStrategy.EXPONENTIAL:
            delay = config.base_delay * (config.backoff_factor ** (attempt - 1))
        elif config.strategy == RetryStrategy.FIBONACCI:
            fib = [1, 1]
            for _ in range(attempt):
                fib.append(fib[-1] + fib[-2])
            delay = config.base_delay * fib[attempt]
        elif config.strategy == RetryStrategy.FIXED:
            delay = config.base_delay
        else:
            delay = config.base_delay
        if config.jitter and _nd_allowed():
            jitter_amount = delay * 0.1
            delay += secrets.SystemRandom().uniform(-jitter_amount, jitter_amount)
        return min(max(0.1, delay), config.max_delay)
    def get_stats(self) -> Dict[str, Any]:
        return {
            "circuit_breakers": {
                name: breaker.get_state()
                for name, breaker in self.breakers.items()
            },
            "retry_stats": dict(self.retry_stats),
            "total_requests": sum(
                stats["success"] + stats["failures"]
                for stats in self.retry_stats.values()
            )
        }