from .__data_feed_base import _DataFeedBase

class DataFeed(_DataFeedBase):
    def surgical_reset_symbol(self, symbol: str) -> None:
        sym = _canon_symbol(symbol)
        now = time.time()
        lg = getattr(self, "_logger", None)
        try:
            ex = getattr(self, "_ex", None)
            fn = getattr(ex, "invalidate_depth_endpoint", None)
            if callable(fn):
                try:
                    fn(sym, reason="surgical_reset")
                except TypeError:
                    fn(sym)
        except Exception as e:
            try:
                if lg:
                    lg.warning("event=SURGICAL_RESET_ENDPOINT_FAIL sym=%s err=%s", sym, str(e)[:220])
            except Exception:
                pass
        cleared = []
        try:
            lk = getattr(self, "_lock", None)
            ctx = lk if lk is not None else contextlib.nullcontext()
            with ctx:
                for name in ("_cache", "_failed_until", "_depth_404_hits", "_dead_warned", "_depth_fail", "_depth_fail_ts"):
                    d = getattr(self, name, None)
                    if isinstance(d, dict) and sym in d:
                        d.pop(sym, None)
                        cleared.append(name)
                for name in ("_failed_symbols", "_failed_markets", "_dead_symbols"):
                    s = getattr(self, name, None)
                    if isinstance(s, set) and sym in s:
                        s.discard(sym)
                        cleared.append(name)
        except Exception as e:
            try:
                if lg:
                    lg.error("event=SURGICAL_RESET_CACHE_FAIL sym=%s err=%s", sym, str(e)[:220])
            except Exception:
                pass
            raise
        try:
            if lg:
                lg.info("event=SURGICAL_RESET_OK sym=%s cleared=%s", sym, ",".join(cleared) if cleared else "-")
        except Exception:
            pass