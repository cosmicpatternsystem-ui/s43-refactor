from .logger import Logger
from .exchange_client import ExchangeClient

class MarketSpecsCache:
    def __init__(self, ex_public: ExchangeClient, logger: logging.Logger):
        self._ex = ex_public
        self._logger = logger
        self._cache: Dict[str, dict] = {}
        self._ts = 0.0
        self._ttl_sec = float(_env_float("META_REFRESH_SEC", 3600.0))
    async def refresh_if_needed(self) -> None:
        now = time.time()
        if self._cache and (now - self._ts) < self._ttl_sec:
            return
        try:
            payload = await self._ex.get_symbols()
            rows = []
            if isinstance(payload, dict):
                for k in ("data", "results", "symbols", "markets", "items"):
                    if isinstance(payload.get(k), list):
                        rows = payload.get(k)
                        break
            if isinstance(payload, list):
                rows = payload
            if not rows:
                return
            out = {}
            for it in rows:
                if not isinstance(it, dict):
                    continue
                nm = _canon_symbol(it.get("name") or it.get("symbol") or "")
                if not nm:
                    continue
                for a in _symbol_aliases(nm):
                    out[_canon_symbol(a)] = it
            self._cache = out
            self._ts = now
        except Exception as e:
            self._logger.warning("Meta refresh failed: %s", e)
    async def get(self, symbol: str) -> dict:
        await self.refresh_if_needed()
        sym = _canon_symbol(symbol)
        for a in _symbol_aliases(sym):
            spec = self._cache.get(_canon_symbol(a))
            if isinstance(spec, dict):
                return spec
        return {}