from .logger import Logger
from .symbol_snapshot import SymbolSnapshot

class MarketSnapshotStore:
    """Central per-symbol snapshot store with explicit quality + reasons.

    """
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._log = logger
        self._by: Dict[str, SymbolSnapshot] = {}
        self._subsys: Dict[str, Dict[str, Any]] = {}  #
    def _get(self, symbol: str) -> SymbolSnapshot:
        s = _canon_symbol(symbol)
        if not s:
            s = str(symbol or "").strip().upper()
        ss = self._by.get(s)
        if ss is None:
            ss = SymbolSnapshot(symbol=s)
            self._by[s] = ss
        return ss
    def update_ok(
        self,
        symbol: str,
        *,
        mid: float,
        ts: float,
        bid: float = 0.0,
        ask: float = 0.0,
        src: str = "",
        quality: Optional[int] = None,
        reason: str = "",
    ) -> None:
        ss = self._get(symbol)
        try:
            ss.ts = float(ts or 0.0)
        except Exception:
            ss.ts = float(time.time())
        try:
            ss.mid = float(mid or 0.0)
        except Exception:
            ss.mid = 0.0
        try:
            ss.bid = float(bid or 0.0)
        except Exception:
            ss.bid = 0.0
        try:
            ss.ask = float(ask or 0.0)
        except Exception:
            ss.ask = 0.0
        ss.status = "OK"
        ss.reason = str(reason or "")
        ss.src = str(src or "")
        try:
            if quality is None:
                q = 100 if (ss.mid > 0.0 and ss.bid > 0.0 and ss.ask > 0.0) else (90 if ss.mid > 0.0 else 0)
                ss.quality = int(clamp(q, 0, 100))
            else:
                ss.quality = int(clamp(int(quality), 0, 100))
        except Exception:
            ss.quality = 0
        ss.last_error = ""
        ss.last_attempt_ts = float(time.time())
        ss.fail_count = 0
    def mark_missing(self, symbol: str, *, reason: str = "NO_TICK") -> None:
        ss = self._get(symbol)
        now = float(time.time())
        new_reason = str(reason or "NO_TICK")
        old_reason = str(getattr(ss, "reason", "") or "")
        old_status = str(getattr(ss, "status", "") or "").upper()
        generic = {"", "NO_TICK", "MISSING"}
        if old_reason and (old_reason.upper() not in generic) and (new_reason.upper() in generic):
            new_reason = old_reason
        if old_status in ("UNSUPPORTED", "ERROR") and (new_reason.upper() in generic):
            try:
                ss.last_attempt_ts = now
                ss.fail_count = int(ss.fail_count or 0) + 1
            except Exception:
                pass
            return
        try:
            grace = float(_env_float("MKT_STORE_MISSING_GRACE_SEC", 8.0) or 8.0)
        except Exception:
            grace = 8.0
        try:
            if ss.status == "OK" and float(ss.ts or 0.0) > 0.0 and float(grace) > 0.0:
                age = float(now) - float(ss.ts)
                if math.isfinite(float(age)) and float(age) <= float(grace):
                    ss.last_error = _short(str(new_reason or "NO_TICK"), 120)
                    ss.last_attempt_ts = float(now)
                    ss.fail_count = int(ss.fail_count or 0) + 1
                    return
        except Exception:
            pass
        ss.status = "MISSING"
        ss.reason = new_reason
        ss.quality = 0
        ss.last_attempt_ts = now
        ss.fail_count = int(ss.fail_count or 0) + 1
        try:
            lim = int(_env_int("MKT_STORE_UNSUPPORTED_AFTER_FAILS", 6) or 6)
        except Exception:
            lim = 6
        try:
            ru = str(new_reason or "").upper()
            evidence = ("UNSUP" in ru) or ("UNRES" in ru) or ("NOT_FOUND" in ru) or ("PAIR" in ru)
            if evidence and int(ss.fail_count or 0) >= int(lim) and float(ss.ts or 0.0) <= 0.0 and float(ss.mid or 0.0) <= 0.0:
                ss.status = "UNSUPPORTED"
                ss.reason = "UNSUPPORTED"
        except Exception:
            pass
    def mark_unsupported(self, symbol: str, *, reason: str = "UNSUPPORTED") -> None:
        ss = self._get(symbol)
        now = float(time.time())
        ss.status = "UNSUPPORTED"
        ss.reason = str(reason or "UNSUPPORTED")
        ss.quality = 0
        ss.last_attempt_ts = now
        ss.fail_count = int(ss.fail_count or 0) + 1
    def mark_error(self, symbol: str, *, reason: str = "ERROR", error: str = "") -> None:
        ss = self._get(symbol)
        now = float(time.time())
        new_reason = str(reason or "ERROR")
        old_reason = str(getattr(ss, "reason", "") or "")
        generic = {"", "NO_TICK", "MISSING"}
        if old_reason and (old_reason.upper() not in generic) and (new_reason.upper() in generic):
            new_reason = old_reason
        ss.status = "ERROR"
        ss.reason = new_reason
        ss.last_error = _short(str(error or ""), 160)
        ss.quality = 0
        ss.last_attempt_ts = now
        ss.fail_count = int(ss.fail_count or 0) + 1
    def should_attempt(
        self,
        symbol: str,
        *,
        now: Optional[float] = None,
        base_sec: float = 6.0,
        cap_sec: float = 120.0,
        min_fail: int = 2,
    ) -> bool:
        """Exponential backoff for repeated failures (tail symbols).

        """
        ss = self._get(symbol)
        try:
            now0 = float(time.time() if now is None else now)
        except Exception:
            now0 = float(time.time())
        try:
            fc = int(getattr(ss, "fail_count", 0) or 0)
        except Exception:
            fc = 0
        if fc < int(min_fail):
            return True
        try:
            last = float(getattr(ss, "last_attempt_ts", 0.0) or 0.0)
        except Exception:
            last = 0.0
        try:
            pow_n = max(0, min(10, int(fc - int(min_fail))))
        except Exception:
            pow_n = 0
        try:
            delay = min(float(cap_sec), float(base_sec) * (2.0 ** float(pow_n)))
        except Exception:
            delay = float(cap_sec)
        if last <= 0.0:
            return True
        return (now0 - last) >= float(delay)
    def get(self, symbol: str) -> SymbolSnapshot:
        return self._get(symbol)
    def stale_symbols(self, *, now: Optional[float] = None, stale_after_sec: float = 15.0, limit: int = 12) -> List[Dict[str, Any]]:
        try:
            now0 = float(time.time() if now is None else now)
        except Exception:
            now0 = float(time.time())
        out: List[Dict[str, Any]] = []
        try:
            items = list(self._by.values())
        except Exception:
            items = []
        for ss in items:
            try:
                age = ss.age_sec(now0)
            except Exception:
                age = float("inf")
            if (not math.isfinite(float(age))) or float(age) > float(stale_after_sec) or ss.status != "OK":
                out.append({
                    "symbol": ss.symbol,
                    "age_sec": (None if not math.isfinite(float(age)) else float(age)),
                    "status": ss.status,
                    "reason": ss.reason,
                    "quality": int(ss.quality or 0),
                    "src": ss.src,
                })
        try:
            out.sort(key=lambda r: (0 if r.get("status") != "OK" else 1, float(r.get("age_sec") or 1e9)), reverse=True)
        except Exception:
            pass
        return out[: max(1, int(limit))]
    def set_subsys(self, name: str, **fields: Any) -> None:
        k = str(name or "").strip().lower()
        if not k:
            return
        d = self._subsys.get(k)
        if d is None:
            d = {}
            self._subsys[k] = d
        try:
            d.update(fields)
        except Exception:
            for kk, vv in (fields or {}).items():
                d[str(kk)] = vv
    def subsys(self, name: str) -> Dict[str, Any]:
        return dict(self._subsys.get(str(name or "").strip().lower(), {}) or {})