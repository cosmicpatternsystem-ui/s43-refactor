from .retry_strategy import RetryStrategy
from .retry_config import RetryConfig
from .adaptive_retry_handler import AdaptiveRetryHandler
from .async_rate_limiter import AsyncRateLimiter

class ResilientAPIClient:
    def __init__(
        self,
        base_url: str,
        rate_limiter: AsyncRateLimiter,
        retry_handler: AdaptiveRetryHandler
    ):
        self.base_url = base_url
        self.rate_limiter = rate_limiter
        self.retry_handler = retry_handler
        self.session: Optional[aiohttp.ClientSession] = None
        self.endpoint_configs = {
            "/market/depth/": RetryConfig(
                strategy=RetryStrategy.EXPONENTIAL,
                max_attempts=3,
                base_delay=1.0,
                max_delay=10.0,
                circuit_breaker_threshold=3
            ),
            "/market/orders/": RetryConfig(
                strategy=RetryStrategy.FIXED,
                max_attempts=2,
                base_delay=2.0,
                max_delay=5.0,
                circuit_breaker_threshold=2
            ),
            "/wallet/balance/": RetryConfig(
                strategy=RetryStrategy.EXPONENTIAL,
                max_attempts=5,
                base_delay=1.5,
                max_delay=30.0,
                circuit_breaker_threshold=5
            )
        }
    async def ensure_session(self):
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            try:
                resolver = aiohttp.AsyncResolver()
            except Exception:
                resolver = aiohttp.DefaultResolver()
            try:
                ttl = int(_env_int("DNS_CACHE_TTL_SEC", 300) or 300)
            except Exception:
                ttl = 300
            connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300, use_dns_cache=True, resolver=resolver)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    "User-Agent": "RazTraderPlus/2.0",
                    "Accept": "application/json"
                }
            )
    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        await self.ensure_session()
        config = self.endpoint_configs.get(
            endpoint,
            RetryConfig(
                strategy=RetryStrategy.EXPONENTIAL,
                max_attempts=3,
                base_delay=1.0,
                max_delay=10.0
            )
        )
        async def _make_request():
            async with self.rate_limiter:
                url = f"{self.base_url}{endpoint}"
                async with self.session.request(method, url, **kwargs) as resp:
                    if resp.status >= 500:
                        text = await resp.text()
                        raise aiohttp.ClientError(
                            f"Server error {resp.status}: {text[:200]}"
                        )
                    elif resp.status == 429:
                        raise aiohttp.ClientError("Rate limited")
                    data = await resp.json()
                    if isinstance(data, dict) and not data.get("ok", True):
                        raise Exception(f"API error: {data.get('error', 'Unknown')}")
                    return data
        return await self.retry_handler.execute_with_retry(
            _make_request,
            endpoint,
            config
        )
    async def reset_session(self) -> bool:
        """Best-effort session reset for watchdog recovery."""
        try:
            await self.close()
        except Exception:
            pass
        try:
            self.session = None
        except Exception:
            pass
        return True
    async def reset_http(self) -> bool:
        return await self.reset_session()
    async def reset_network(self) -> bool:
        return await self.reset_session()
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()