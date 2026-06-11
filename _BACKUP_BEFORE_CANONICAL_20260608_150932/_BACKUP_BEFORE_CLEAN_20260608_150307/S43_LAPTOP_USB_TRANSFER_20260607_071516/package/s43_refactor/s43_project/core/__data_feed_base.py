from .order_book_top import OrderBookTop
from .logger import Logger
from .temporary_pause import TemporaryPause
from .exchange_client import ExchangeClient
from .data_feed import DataFeed

class _DataFeedBase:
    def __init__(self, ex: ExchangeClient, logger: logging.Logger, ttl_sec: float = 1.2, price_cache_path: str = "raz_price_cache.json"):
        self._ex = ex
        self._logger = logger
        self._ttl = float(ttl_sec)
        self._cache: Dict[str, Tuple[float, OrderBookTop]] = {}
        self._spot_cache: Dict[str, Tuple[float, float]] = {}
        self._price_cache_path = price_cache_path
        self._disk_cache: Dict[str, dict] = self._load_price_cache()
        self._jitter_proxy = _env_bool("JITTER_PROXY", False)
        self._jitter_ttl_mult = max(1.0, _env_float("JITTER_TTL_MULT", 2.0))
        self._jitter_samples = max(1, _env_int("JITTER_SAMPLES", 5))
        self._mid_hist: Dict[str, deque] = {}
        self._failed_symbols = set()
        self._failed_until: Dict[str, float] = {}
        self._depth_404_hits: Dict[str, int] = {}
        self._failed_markets = self._failed_symbols
        self._dead_symbols = self._failed_symbols
        self._dead_warned: Dict[str, float] = {}
        self._depth_fail: Dict[str, dict] = {}
    def _load_price_cache(self) -> Dict[str, dict]:
        try:
            if not os.path.isfile(self._price_cache_path):
                return {}
            with open(self._price_cache_path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            if not isinstance(obj, dict):
                return {}
            now = float(time.time())
            try:
                max_age = float(_env_float("PRICE_CACHE_MAX_AGE_SEC", 180.0) or 180.0)
            except Exception:
                max_age = 180.0
            if max_age > 0.0 and math.isfinite(max_age):
                stale_keys = []
                for k, v in obj.items():
                    try:
                        if not isinstance(v, dict):
                            stale_keys.append(k)
                            continue
                        ts = float(v.get("ts") or 0.0)
                        if ts <= 0.0 or (now - ts) > max_age:
                            stale_keys.append(k)
                    except Exception:
                        stale_keys.append(k)
                for k in stale_keys:
                    obj.pop(k, None)
            return obj
        except Exception:
            return {}
    def _save_price_cache(self) -> None:
        try:
            _ensure_dir(self._price_cache_path)
            with open(self._price_cache_path, "w", encoding="utf-8") as f:
                json.dump(self._disk_cache, f, ensure_ascii=False)
        except Exception:
            pass
    @staticmethod
    def _parse_depth(depth: Any) -> Optional[OrderBookTop]:
        obj = depth or {}
        data = None
        if isinstance(obj, dict):
            for k in ("data", "result", "results", "orderbook", "orderBook", "order_book", "book"):
                v = obj.get(k)
                if isinstance(v, (dict, list)) and v:
                    data = v
                    break
        if data is None:
            data = obj
        bids: Any = []
        asks: Any = []
        if isinstance(data, dict):
            bids = data.get("bids") or data.get("buy") or data.get("buys") or data.get("bid") or []
            asks = data.get("asks") or data.get("sell") or data.get("sells") or data.get("ask") or []
            if (not bids or not asks):
                for kk in ("orderBook", "orderbook", "order_book", "book"):
                    vv = data.get(kk)
                    if isinstance(vv, dict):
                        bids = bids or vv.get("bids") or vv.get("buy") or vv.get("buys") or []
                        asks = asks or vv.get("asks") or vv.get("sell") or vv.get("sells") or []
        elif isinstance(data, list) and data:
            for x in data[:2]:
                if isinstance(x, dict):
                    b0 = x.get("bids") or x.get("buy") or x.get("buys") or []
                    a0 = x.get("asks") or x.get("sell") or x.get("sells") or []
                    if b0 and a0:
                        bids, asks = b0, a0
                        break
        def _normalize_levels(levels: Any, side: str) -> List[Any]:
            if levels is None:
                return []
            if isinstance(levels, (list, tuple)):
                out0 = list(levels)
                # Core fix: ensure best bid/ask selection is deterministic even if the exchange returns unsorted arrays.
                try:
                    def _p(lvl: Any) -> float:
                        try:
                            if isinstance(lvl, dict):
                                for kk in ("price", "p", "rate", "r", "px", "0"):
                                    if kk in lvl:
                                        return float(_safe_float(lvl.get(kk), 0.0) or 0.0)
                                return 0.0
                            if isinstance(lvl, (list, tuple)) and len(lvl) >= 1:
                                return float(_safe_float(lvl[0], 0.0) or 0.0)
                        except TradingHalt:
                            raise
                        except Exception:
                            return 0.0
                        return 0.0
                    out0.sort(key=_p, reverse=(side == "bids"))
                except Exception:
                    pass
                return out0
            if isinstance(levels, dict):
                for kk in ("levels", "data", "rows", "items", "bids", "asks", "buy", "sell", "buys", "sells"):
                    vv = levels.get(kk)
                    if isinstance(vv, (list, tuple)) and vv:
                        return _normalize_levels(vv, side)
                items = list(levels.items())
                out: List[Any] = []
                if items and all(isinstance(v, dict) for _, v in items):
                    for k, v in items:
                        if not isinstance(v, dict):
                            continue
                        px = _safe_float(v.get("price") or v.get("p") or v.get("rate") or v.get("0") or k, 0.0) or 0.0
                        qty = _safe_float(v.get("amount") or v.get("qty") or v.get("quantity") or v.get("size") or v.get("q") or v.get("1") or v.get("volume") or v.get("v"), 0.0) or 0.0
                        if px > 0.0:
                            out.append([float(px), float(qty)])
                else:
                    for k, v in items:
                        px = _safe_float(k, 0.0) or 0.0
                        qty = _safe_float(v, 0.0) if not isinstance(v, dict) else _safe_float(v.get("amount") or v.get("qty") or v.get("quantity") or v.get("size") or v.get("q") or v.get("1") or v.get("volume") or v.get("v"), 0.0)
                        qty = qty or 0.0
                        if px > 0.0:
                            out.append([float(px), float(qty)])
                if out:
                    out.sort(key=lambda x: float(x[0]), reverse=(side == "bids"))
                return out
            return []
        bids = _normalize_levels(bids, "bids")
        asks = _normalize_levels(asks, "asks")
        last_trade_px = 0.0
        try:
            lt_src = None
            if isinstance(data, dict):
                lt_src = data.get("last_trade") or data.get("lastTrade") or data.get("last") or data.get("last_price") or data.get("lastPrice")
            if lt_src is None and isinstance(obj, dict):
                lt_src = obj.get("last_trade") or obj.get("lastTrade") or obj.get("last") or obj.get("last_price") or obj.get("lastPrice")
            if isinstance(lt_src, dict):
                last_trade_px = float(_safe_float(lt_src.get("price") or lt_src.get("p") or lt_src.get("rate") or lt_src.get("last"), 0.0) or 0.0)
            else:
                last_trade_px = float(_safe_float(lt_src, 0.0) or 0.0)
        except Exception:
            last_trade_px = 0.0
        def _lvl_price(lvl: Any) -> float:
            try:
                if isinstance(lvl, dict):
                    for kk in ("price", "p", "rate", "r", "px", "0"):
                        if kk in lvl:
                            return float(lvl.get(kk) or 0.0)
                    return 0.0
                if isinstance(lvl, (list, tuple)) and len(lvl) >= 1:
                    return float(lvl[0] or 0.0)
            except TradingHalt:
                raise
            except Exception:
                return 0.0
            return 0.0
        bid = _lvl_price(bids[0]) if isinstance(bids, (list, tuple)) and bids else 0.0
        ask = _lvl_price(asks[0]) if isinstance(asks, (list, tuple)) and asks else 0.0
        if bid <= 0.0 and isinstance(bids, list) and bids:
            try:
                for lvl in bids[:8]:
                    bp = _lvl_price(lvl)
                    if bp > 0.0:
                        bid = bp
                        break
            except Exception:
                pass
        if ask <= 0.0 and isinstance(asks, list) and asks:
            try:
                for lvl in asks[:8]:
                    ap = _lvl_price(lvl)
                    if ap > 0.0:
                        ask = ap
                        break
            except Exception:
                pass
        if bid <= 0.0 and ask <= 0.0 and last_trade_px > 0.0:
            bid = ask = last_trade_px
        elif bid <= 0.0 and ask > 0.0:
            bid = ask
        elif ask <= 0.0 and bid > 0.0:
            ask = bid
        # Core safety: protect against crossed/inverted books (bid > ask).
        # Try to repair by selecting a consistent bid/ask from nearby levels; otherwise reject the book.
        if bid > 0.0 and ask > 0.0 and bid > ask:
            try:
                ask2 = 0.0
                if isinstance(asks, list):
                    for lvl in asks[:15]:
                        ap = _lvl_price(lvl)
                        if ap > 0.0 and ap >= bid:
                            ask2 = float(ap)
                            break
                bid2 = 0.0
                target_ask = float(ask2) if ask2 > 0.0 else float(ask)
                if isinstance(bids, list):
                    for lvl in bids[:15]:
                        bp = _lvl_price(lvl)
                        if bp > 0.0 and bp <= target_ask:
                            bid2 = float(bp)
                            break
                if bid2 > 0.0 and ask2 > 0.0 and bid2 <= ask2:
                    bid, ask = float(bid2), float(ask2)
                else:
                    return None
            except TradingHalt:
                raise
            except Exception:
                return None
        mid = (bid + ask) / 2.0 if (bid > 0.0 and ask > 0.0) else (bid if bid > 0.0 else (ask if ask > 0.0 else 0.0))
        if mid <= 0.0:
            return None
        return OrderBookTop(
            bid=float(bid),
            ask=float(ask),
            mid=float(mid),
            spread_bps=(spread_bps(float(bid), float(ask)) if (float(bid) > 0.0 and float(ask) > 0.0) else 0.0),
            bids=list(bids) if isinstance(bids, list) else [],
            asks=list(asks) if isinstance(asks, list) else [],
            last_trade_price=(float(last_trade_px) if last_trade_px > 0.0 else None),
        )
    @staticmethod
    def _is_http_404(exc: Exception) -> bool:
        try:
            msg = str(exc or "")
        except Exception:
            return False
        msg = msg.strip()
        return ("HTTP 404" in msg) or msg.startswith("404")
    def is_ignored(self, symbol: str) -> bool:
        sym = _canon_symbol(symbol)
        try:
            fu = getattr(self, "_failed_until", None)
            if isinstance(fu, dict):
                until = float(fu.get(sym, 0.0) or 0.0)
                if until > 0.0:
                    if time.time() < until:
                        return True
                    try:
                        fu.pop(sym, None)
                    except Exception:
                        pass
                    try:
                        self._failed_symbols.discard(sym)
                    except Exception:
                        pass
        except Exception:
            pass
        return sym in getattr(self, "_failed_symbols", set())
    def _blacklist_symbol(self, symbol: str, reason: str) -> None:
        sym = _canon_symbol(symbol)
        try:
            ttl = float(os.getenv("SYMBOL_TEMP_BLACKLIST_TTL_SEC", os.getenv("SOFT_BLACKLIST_TTL_SEC", "300.0")) or 300.0)
        except Exception:
            ttl = 300.0
        ttl = float(max(30.0, min(3600.0, ttl)))
        until = float(time.time() + ttl)
        try:
            self._dead_symbols.add(sym)
        except Exception:
            pass
        try:
            self._failed_symbols.add(sym)
        except Exception:
            pass
        try:
            self._failed_until[sym] = until
        except Exception:
            pass
        try:
            now = float(time.time())
            last = float(self._dead_warned.get(sym, 0.0) or 0.0)
            if (now - last) > max(60.0, ttl * 0.5):
                self._dead_warned[sym] = now
                self._logger.warning("event=SYMBOL_TEMP_BLACKLIST sym=%s reason=%s ttl=%.0fs", sym, str(reason or "blacklisted"), ttl)
        except Exception:
            pass
        try:
            self._cache.pop(sym, None)
        except Exception:
            pass
    def _depth_note_ok(self, sym: str, now: Optional[float] = None) -> None:
        try:
            sym = _canon_symbol(sym)
            now = float(time.time() if now is None else now)
            rec = self._depth_fail.get(sym) if hasattr(self, "_depth_fail") else None
            if rec is None:
                self._depth_fail[sym] = {"streak": 0, "last_fail_ts": 0.0, "last_ok_ts": now, "last_err": ""}
                return
            rec["streak"] = 0
            rec["last_ok_ts"] = now
        except Exception:
            return
    def _depth_note_fail(self, sym: str, err: str, now: Optional[float] = None) -> None:
        try:
            sym = _canon_symbol(sym)
            now = float(time.time() if now is None else now)
            if not hasattr(self, "_depth_fail"):
                self._depth_fail = {}
            rec = self._depth_fail.get(sym)
            if rec is None:
                rec = {"streak": 0, "last_fail_ts": 0.0, "last_ok_ts": 0.0, "last_err": ""}
                self._depth_fail[sym] = rec
            rec["streak"] = int(rec.get("streak", 0) or 0) + 1
            rec["last_fail_ts"] = now
            rec["last_err"] = str(err or "")[:220]
        except Exception:
            return
    def depth_fail_snapshot(self) -> Dict[str, dict]:
        try:
            return dict(getattr(self, "_depth_fail", {}) or {})
        except Exception:
            return {}
    async def fetch_depth(self, symbol: str, use_disk_cache_on_timeout: bool = True, force_refresh: bool = False, bypass_ignore: bool = False, priority: bool = False) -> Optional[OrderBookTop]:
        sym = _canon_symbol(symbol)
        now = time.time()
        if self.is_ignored(sym) and (not bool(bypass_ignore)):
            return None
        cached = None if bool(force_refresh) else self._cache.get(sym)
        if cached is not None:
            ts, ob = cached
            try:
                eff_ttl = self._ttl * (self._jitter_ttl_mult if self._jitter_proxy else 1.0)
            except Exception:
                eff_ttl = self._ttl
            if (now - ts) <= eff_ttl:
                try:
                    setattr(ob, "ts", float(ts))
                    setattr(ob, "age_sec", max(0.0, float(now) - float(ts)))
                    setattr(ob, "_source", "mem_cache")
                except Exception:
                    pass
                try:
                    self._depth_note_ok(sym, now)
                except Exception:
                    pass
                return ob
        msg = ""
        try:
            to_total = float(os.getenv("DEPTH_FETCH_TIMEOUT_SEC", "") or 0.0)
        except Exception:
            to_total = 0.0
        if to_total <= 0.0:
            try:
                per_to = float(os.getenv("DEPTH_REQ_TIMEOUT_SEC", os.getenv("DEPTH_TIMEOUT_SEC", "7.0" if _env_bool("TERMUX_MODE", False) else "5.0")) or 5.0)
            except Exception:
                per_to = 5.0
            try:
                retry_max = int(os.getenv("DEPTH_RETRY_MAX", "4" if _env_bool("TERMUX_MODE", False) else "3") or 3)
            except Exception:
                retry_max = 3
            retry_max = max(1, min(8, int(retry_max)))
            to_total = float(per_to) * (1.8 if retry_max >= 3 else 1.4) + 2.0
            to_total = min(30.0, max(4.0, to_total))
        to_total = max(2.5, float(to_total))
        deadline = now + float(to_total)
        try:
            retry_max = int(os.getenv("DEPTH_RETRY_MAX", "4" if _env_bool("TERMUX_MODE", False) else "3") or 3)
        except Exception:
            retry_max = 3
        retry_max = max(1, min(8, int(retry_max)))
        try:
            backoff0 = float(os.getenv("DEPTH_RETRY_BACKOFF_SEC", "0.25") or 0.25)
        except Exception:
            backoff0 = 0.25
        backoff0 = max(0.05, float(backoff0))
        try:
            fail_n = int(os.getenv("DEPTH_404_FAIL_N", "12") or 12)
        except Exception:
            fail_n = 12
        fail_n = max(3, int(fail_n))
        try:
            hard_fail_ttl = float(os.getenv("DEPTH_HARD_FAIL_TTL_SEC", "3600" if _env_bool("TERMUX_MODE", False) else "1800") or 1800.0)
        except Exception:
            hard_fail_ttl = 1800.0
        hard_fail_ttl = max(60.0, float(hard_fail_ttl))
        last_exc: Optional[Exception] = None
        for attempt in range(int(retry_max)):
            if time.time() > deadline:
                msg = "timeout"
                break
            try:
                raw = await self._ex.get_depth(sym, priority=bool(priority))
                top = self._parse_depth(raw)
                if top is None:
                    raise ValueError("DEPTH_PARSE_FAIL")
                try:
                    self._depth_404_hits.pop(sym, None)
                except Exception:
                    pass
                now2 = time.time()
                try:
                    setattr(top, "ts", float(now2))
                    setattr(top, "age_sec", 0.0)
                    setattr(top, "_source", "live")
                except Exception:
                    pass
                self._cache[sym] = (now2, top)
                try:
                    hist = self._mid_hist.setdefault(sym, __import__("collections").deque(maxlen=int(self._jitter_samples)))
                    hist.append(float(top.mid))
                except Exception:
                    pass
                try:
                    self._disk_cache[sym] = {
                        "ts": now2,
                        "bid": top.bid,
                        "ask": top.ask,
                        "mid": top.mid,
                        "spr_bps": top.spread_bps,
                    }
                    self._save_price_cache()
                except Exception:
                    pass
                try:
                    self._depth_note_ok(sym, now2)
                except Exception:
                    pass
                return top
            except (TradingHalt, TemporaryPause):
                raise
            except asyncio.TimeoutError as e:
                last_exc = e
                msg = "timeout"
            except Exception as e:
                last_exc = e
                try:
                    msg = str(e or "").strip()
                except Exception:
                    msg = ""
                low = msg.lower()
                try:
                    is_404 = self._is_http_404(e)
                except Exception:
                    is_404 = ("404" in msg)
                if is_404 or ("not found" in low):
                    try:
                        if hasattr(self._ex, "invalidate_depth_endpoint"):
                            self._ex.invalidate_depth_endpoint(sym, reason="HTTP_404")
                    except Exception:
                        pass
                    try:
                        hits = int(self._depth_404_hits.get(sym, 0) or 0) + 1
                        self._depth_404_hits[sym] = hits
                    except Exception:
                        hits = 1
                    try:
                        self._logger.warning("event=DEPTH_HTTP404 sym=%s hits=%d err=%s", sym, int(hits), msg[:160])
                    except Exception:
                        pass
                    if int(hits) >= int(fail_n):
                        try:
                            self._logger.critical("event=DEPTH_SYMBOL_HARD_IGNORE sym=%s hits=%d ttl=%.0fs", sym, int(hits), float(hard_fail_ttl))
                        except Exception:
                            pass
                        try:
                            self._failed_symbols.add(sym)
                            self._failed_until[sym] = float(time.time() + float(hard_fail_ttl))
                        except Exception:
                            pass
                        try:
                            self._blacklist_symbol(sym, "HTTP_404_REPEATED")
                        except Exception:
                            pass
                        return None
            if attempt < (retry_max - 1):
                try:
                    dt = min(1.2, backoff0 * (2 ** attempt))
                    await asyncio.sleep(dt)
                except Exception:
                    pass
        if use_disk_cache_on_timeout:
            dc = self._disk_cache.get(sym)
            if dc:
                try:
                    max_age = float(_env_float("DEPTH_DISK_CACHE_MAX_AGE_SEC", (90.0 if _env_bool("TERMUX_MODE", False) else 60.0)) or 0.0)
                except Exception:
                    max_age = 0.0
                try:
                    dc_ts = float(dc.get("ts") or 0.0)
                except Exception:
                    dc_ts = 0.0
                try:
                    if max_age > 0.0 and dc_ts > 0.0 and (now - dc_ts) > max_age:
                        try:
                            self._disk_cache.pop(sym, None)
                        except Exception:
                            pass
                        dc = None
                except Exception:
                    pass
            if dc:
                try:
                    bid = float(dc.get("bid") or 0.0)
                    ask = float(dc.get("ask") or 0.0)
                    mid = float(dc.get("mid") or 0.0)
                    if bid > 0 and ask > 0 and mid > 0:
                        ob = OrderBookTop(
                            bid=bid,
                            ask=ask,
                            mid=mid,
                            spread_bps=float(dc.get("spr_bps") or spread_bps(bid, ask)),
                            bids=[],
                            asks=[],
                        )
                        try:
                            setattr(ob, "ts", float(dc_ts or now))
                            setattr(ob, "age_sec", max(0.0, float(now) - float(dc_ts or now)))
                            setattr(ob, "_source", "disk_cache")
                            setattr(ob, "_stale", True)
                        except Exception:
                            pass
                        try:
                            self._depth_note_fail(sym, (str(msg) if msg else "DISK_CACHE_FALLBACK"), now=now)
                        except Exception:
                            pass
                        return ob
                except Exception:
                    pass
        try:
            self._depth_note_fail(sym, str(msg))
        except Exception:
            pass
        try:
            self._logger.error("event=DEPTH_FETCH_FAIL sym=%s err=%s", sym, str(msg)[:200])
        except Exception:
            pass
        try:
            tmo2 = float(os.getenv("DEPTH_SYNTH_SPOT_TIMEOUT_SEC", "2.5") or 2.5)
        except Exception:
            tmo2 = 2.5
        try:
            px = await asyncio.wait_for(self.fetch_spot(sym), timeout=max(1.0, min(8.0, float(tmo2))))
        except Exception:
            px = None
        if px is not None:
            try:
                px_f = float(px)
            except Exception:
                px_f = 0.0
            if px_f > 0.0:
                try:
                    sbps = float(os.getenv("DEPTH_SYNTH_SPREAD_BPS", "120.0") or 120.0)
                except Exception:
                    sbps = 120.0
                sbps = float(max(10.0, min(1500.0, sbps)))
                half = sbps / 20000.0
                bid = px_f * (1.0 - half)
                ask = px_f * (1.0 + half)
                try:
                    ob = OrderBookTop(
                        bid=float(bid),
                        ask=float(ask),
                        mid=float(px_f),
                        spread_bps=float(sbps),
                        bids=[],
                        asks=[],
                    )
                    try:
                        setattr(ob, "ts", float(now))
                        setattr(ob, "age_sec", float("inf"))
                        setattr(ob, "_source", "synth_spot")
                        setattr(ob, "_stale", True)
                    except Exception:
                        pass
                    try:
                        self._cache[sym] = (float(now), ob)
                    except Exception:
                        pass
                    try:
                        self._disk_cache[sym] = {
                            "ts": float(now),
                            "bid": float(bid),
                            "ask": float(ask),
                            "mid": float(px_f),
                            "spread_bps": float(sbps),
                        }
                    except Exception:
                        pass
                    return ob
                except Exception:
                    pass
        return None
    async def fetch_spot(self, symbol: str) -> Optional[float]:
        'Best-effort spot price (mid) for a symbol.'
        sym = _canon_symbol(symbol)
        now = time.time()
        ttl = float(max(2.0, float(getattr(self, "_ttl", 6.0) or 6.0)))
        cached = self._spot_cache.get(sym)
        try:
            if cached is not None:
                ts, px0 = cached
                if float(px0 or 0.0) > 0.0 and (now - float(ts)) <= ttl:
                    return float(px0)
        except Exception:
            cached = None
        hist_max = int(getattr(self, "_hist_max", int(_env_int("MID_HIST_MAX", 120) or 120)) or 120)
        def _px_from_row(row: Any) -> Optional[float]:
            if isinstance(row, dict) and isinstance(row.get("raw"), dict):
                row = row.get("raw")
            if isinstance(row, dict):
                keys = (
                    "last", "last_price", "lastPrice",
                    "last_trade", "lastTrade", "lastTradePrice",
                    "last_traded_price", "last_traded", "final",
                    "price", "current", "currentPrice", "current_price",
                    "close", "closePrice", "close_price",
                    "c", "p", "rate", "value", "latest", "latest_price",
                )
                for k in keys:
                    if k in row and row.get(k) is not None:
                        v = _safe_float(row.get(k), default=0.0, translate_digits=True, allow_percent=False, finite=True, na_values=True, strip=True)
                        if v > 0.0:
                            return float(v)
                for kk in ("data", "result", "ticker", "stats", "market", "payload"):
                    vv = row.get(kk)
                    if isinstance(vv, dict):
                        out = _px_from_row(vv)
                        if out:
                            return out
            if isinstance(row, (int, float)) and float(row) > 0.0:
                return float(row)
            if isinstance(row, str):
                v = _safe_float(row, default=0.0, translate_digits=True, allow_percent=False, finite=True, na_values=True, strip=True)
                if v > 0.0:
                    return float(v)
            return None
        def _try_snapshots() -> Optional[float]:
            snap = getattr(self._ex, "_last_market_stats_snapshot", None)
            if isinstance(snap, dict) and snap:
                for s0 in (_symbol_aliases(sym) or [sym]):
                    s1 = _canon_symbol(s0)
                    row = snap.get(s1) or snap.get(s0)
                    px = _px_from_row(row)
                    if px:
                        return float(px)
            snap2 = getattr(self._ex, "_last_all_tickers_snapshot", None)
            if isinstance(snap2, dict) and snap2:
                by = snap2.get("by_symbol") if isinstance(snap2.get("by_symbol"), dict) else snap2
                if isinstance(by, dict):
                    for s0 in (_symbol_aliases(sym) or [sym]):
                        s1 = _canon_symbol(s0)
                        row = by.get(s1) or by.get(s0)
                        px = _px_from_row(row)
                        if px:
                            return float(px)
            return None
        async def _refresh_snapshots_once() -> None:
            try:
                tmo = float(_env_float("SPOT_SNAPSHOT_TIMEOUT_SEC", _env_float("TICKERS_REQ_TIMEOUT", 6.5)) or 6.5)
            except Exception:
                tmo = 6.5
            try:
                await asyncio.wait_for(self._ex.get_market_snapshot(), timeout=tmo)
            except (TradingHalt, TemporaryPause):
                raise
            except Exception:
                pass
            try:
                await asyncio.wait_for(self._ex.get_all_tickers_optimized(), timeout=tmo)
            except (TradingHalt, TemporaryPause):
                raise
            except Exception:
                pass
        px = _try_snapshots()
        if (px is None) or float(px or 0.0) <= 0.0:
            try:
                await _refresh_snapshots_once()
            except (TradingHalt, TemporaryPause):
                raise
            except Exception:
                pass
            px = _try_snapshots()
        if (px is None) or float(px or 0.0) <= 0.0:
            try:
                tmo = float(_env_float("TRADES_REQ_TIMEOUT", _env_float("TICKERS_REQ_TIMEOUT", 6.5)) or 5.0)
            except Exception:
                tmo = 5.0
            try:
                candidates = _symbol_aliases(sym) or [sym]
                for cand in candidates[:12]:
                    raw = await asyncio.wait_for(self._ex.get_trades(_canon_symbol(cand)), timeout=tmo)
                    data = (raw.get("data") if isinstance(raw, dict) else raw) or raw
                    if isinstance(data, dict) and "data" in data and isinstance(data.get("data"), list):
                        data = data.get("data")
                    if not isinstance(data, list) or not data:
                        continue
                    t_last = data[0] if isinstance(data[0], dict) else None
                    try:
                        if isinstance(data[-1], dict) and isinstance(t_last, dict):
                            ts0 = t_last.get("time") or t_last.get("timestamp") or t_last.get("ts")
                            ts1 = data[-1].get("time") or data[-1].get("timestamp") or data[-1].get("ts")
                            if ts1 and ts0 and _safe_float(ts1) > _safe_float(ts0):
                                t_last = data[-1]
                    except Exception:
                        pass
                    px_t = _px_from_row(t_last or {})
                    if px_t and float(px_t) > 0.0:
                        px = float(px_t)
                        break
            except (TradingHalt, TemporaryPause):
                raise
            except Exception:
                px = None
        if (px is None) or float(px or 0.0) <= 0.0:
            try:
                s = sym
                q = None
                for quote in ("IRT", "IRR", "USDT", "USD", "USDC"):
                    if s.endswith(quote) and len(s) > len(quote):
                        q = quote
                        base = s[: -len(quote)]
                        break
                if q in ("IRT", "IRR") and base and base not in ("USDT", "USD", "USDC"):
                    base_usdt = _canon_symbol(base + "USDT")
                    usdt_quote = _canon_symbol("USDT" + q)
                    px_base = await self.fetch_spot(base_usdt)
                    px_usdt = await self.fetch_spot(usdt_quote)
                    if px_base and px_usdt and float(px_base) > 0.0 and float(px_usdt) > 0.0:
                        px = float(px_base) * float(px_usdt)
            except Exception:
                px = None
        try:
            if px is not None and float(px or 0.0) > 0.0:
                self._spot_cache[sym] = (now, float(px))
                try:
                    dq = self._mid_hist.setdefault(sym, __import__("collections").deque(maxlen=hist_max))
                    dq.append(float(px))
                except Exception:
                    pass
                return float(px)
        except Exception:
            pass
        try:
            if cached is not None:
                ts, px0 = cached
                max_stale = max(180.0, 5.0 * float(ttl))
                if float(px0 or 0.0) > 0.0 and (now - float(ts)) <= max_stale:
                    return float(px0)
        except Exception:
            pass
        return None
    async def fetch_depths(self, symbols: List[str], use_disk_cache_on_timeout: bool = True) -> Dict[str, OrderBookTop]:
        active: List[str] = []
        seen = set()
        for s in symbols:
            sym = _canon_symbol(s)
            if sym in seen:
                continue
            seen.add(sym)
            if sym in getattr(self, "_failed_symbols", set()):
                try:
                    if bool(self.is_ignored(sym)):
                        continue
                    try:
                        getattr(self, "_failed_symbols", set()).discard(sym)
                    except Exception:
                        pass
                except Exception:
                    pass
            active.append(sym)
        if not active:
            return {}
        coros = [self.fetch_depth(sym, use_disk_cache_on_timeout=use_disk_cache_on_timeout) for sym in active]
        results = await asyncio.gather(*coros, return_exceptions=True)
        out: Dict[str, OrderBookTop] = {}
        for sym, r in zip(active, results):
            if isinstance(r, TradingHalt):
                raise r
            if isinstance(r, Exception):
                try:
                    self._depth_note_fail(sym, f"{type(r).__name__}: {str(r) or ''}")
                except Exception:
                    pass
                try:
                    self._logger.error("event=DEPTH_FETCH_FAIL sym=%s err=%s", sym, str(r)[:200])
                except Exception:
                    pass
                continue
            if r is None:
                continue
            out[_canon_symbol(sym)] = r
        return out
    def peek_mid(self, symbol: str) -> Optional[float]:
        sym0 = _canon_symbol(symbol)
        try:
            if getattr(self, "_jitter_proxy", False):
                hist = self._mid_hist.get(sym0)
                if hist:
                    xs = sorted(float(x) for x in hist if float(x) > 0)
                    if xs:
                        return float(xs[len(xs) // 2])
        except Exception:
            pass
        keys: List[str] = []
        try:
            keys.append(sym0)
            ex = getattr(self, "_ex", None)
            cfg = getattr(ex, "cfg", None) if ex is not None else getattr(self, "cfg", None)
            q = str(getattr(cfg, "quote", "") or "").strip().upper()
            if not q:
                q = "IRT"
            try:
                if sym0.endswith(q) and len(sym0) > len(q):
                    base = _canon_symbol(sym0[: -len(q)])
                    if base and base not in keys:
                        keys.append(base)
                else:
                    pair = _canon_pair(sym0, default_quote=q)
                    if pair and pair not in keys:
                        keys.append(pair)
                    if pair.endswith(q) and len(pair) > len(q):
                        base2 = _canon_symbol(pair[: -len(q)])
                        if base2 and base2 not in keys:
                            keys.append(base2)
            except Exception:
                pass
        except Exception:
            keys = [sym0]
        for k in keys:
            try:
                cached = self._cache.get(k)
                if cached is not None:
                    _ts, ob = cached if isinstance(cached, (tuple, list)) and len(cached) >= 2 else (0.0, cached)
                    mid = float(getattr(ob, "mid", 0.0) or 0.0)
                    if mid > 0.0:
                        return mid
            except Exception:
                pass
            try:
                spot = self._spot_cache.get(k)
                if spot is not None and isinstance(spot, (tuple, list)) and len(spot) >= 2:
                    mid = float(spot[1] or 0.0)
                    if mid > 0.0:
                        return mid
            except Exception:
                pass
        for k in keys:
            try:
                dc = self._disk_cache.get(k) or {}
                mid = float(dc.get("mid") or 0.0)
                if mid > 0.0:
                    return mid
            except Exception:
                pass
        return None