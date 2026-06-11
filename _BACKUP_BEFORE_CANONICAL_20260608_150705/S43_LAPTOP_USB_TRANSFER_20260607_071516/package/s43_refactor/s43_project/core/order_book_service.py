from .order_book_top import OrderBookTop
from .logger import Logger
from .data_feed import DataFeed

class OrderBookService:
    def __init__(self, feed: "DataFeed", logger: logging.Logger):
        self._feed = feed
        self._log = logger
        self._inflight: Dict[str, asyncio.Task] = {}
        self._last_ok_ts: Dict[str, float] = {}
        self._last_err: Dict[str, str] = {}
        self._lock = asyncio.Lock()
    def peek(self, symbol: str) -> Optional["OrderBookTop"]:
        try:
            sym = _canon_symbol(symbol)
            c = getattr(self._feed, "_cache", None) or {}
            rec = c.get(sym)
            if rec is None:
                return None
            _ts, ob = rec
            return ob
        except Exception:
            return None
    def last_error(self, symbol: str) -> str:
        try:
            return str(self._last_err.get(_canon_symbol(symbol), "") or "")
        except Exception:
            return ""
    def request_refresh(self, symbol: str, *, use_disk_cache_on_timeout: bool = True, force_refresh: bool = False) -> None:
        sym = _canon_symbol(symbol)
        try:
            t = self._inflight.get(sym)
            if t is not None and not t.done():
                return
            self._inflight[sym] = asyncio.create_task(self._worker(sym, use_disk_cache_on_timeout, force_refresh))
        except Exception:
            return
    async def _worker(self, sym: str, use_disk_cache_on_timeout: bool, force_refresh: bool) -> None:
        try:
            tmo = float(os.getenv("DEPTH_WORKER_TIMEOUT_SEC", "") or 0.0)
        except Exception:
            tmo = 0.0
        if tmo <= 0.0:
            try:
                tmo = float(os.getenv("DEPTH_FETCH_TIMEOUT_SEC", "") or 0.0)
            except Exception:
                tmo = 0.0
        if tmo <= 0.0:
            tmo = 20.0
        tmo = max(3.0, min(45.0, float(tmo)))
        base = 0.35
        cap = 4.0
        tries = 0
        for _omega_guard in range(1000000):
            tries += 1
            try:
                await asyncio.wait_for(
                    self._feed.fetch_depth(sym, use_disk_cache_on_timeout=use_disk_cache_on_timeout, force_refresh=force_refresh),
                    timeout=tmo,
                )
                self._last_ok_ts[sym] = float(time.time())
                self._last_err[sym] = ""
                return
            except asyncio.CancelledError:
                return
            except Exception as e:
                self._last_err[sym] = f"{type(e).__name__}:{e}"
                if tries >= 5:
                    return
                sleep_s = min(cap, base * (2 ** (tries - 1)))
                sleep_s = float(sleep_s) * float(0.85 + (int.from_bytes(hashlib.blake2b(f"{sym}:{tries}".encode(), digest_size=2).digest(), "big") / 65535.0) * 0.3)
                try:
                    await asyncio.sleep(sleep_s)
                except asyncio.CancelledError:
                    return