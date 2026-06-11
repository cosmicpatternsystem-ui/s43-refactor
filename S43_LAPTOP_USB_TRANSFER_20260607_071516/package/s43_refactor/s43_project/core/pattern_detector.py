from .logger import Logger
from .price_history import PriceHistory
from .bot_config import BotConfig

class PatternDetector:
    def __init__(self, cfg: BotConfig, logger: logging.Logger):
        self.cfg = cfg
        self._log = logger
        self.lookback = int(getattr(cfg, "pattern_lookback_bars", 50) or 50)
    @staticmethod
    def _find_local_extremes(prices: List[float], window: int = 5) -> Tuple[List[int], List[int]]:
        peaks: List[int] = []
        troughs: List[int] = []
        if len(prices) < 2 * window + 1:
            return peaks, troughs
        for i in range(window, len(prices) - window):
            local = prices[i - window : i + window + 1]
            if prices[i] == max(local):
                peaks.append(i)
            if prices[i] == min(local):
                troughs.append(i)
        return peaks, troughs
    def detect_double_top(self, highs: List[float], closes: List[float]) -> Optional[Dict[str, Any]]:
        if len(highs) < self.lookback:
            return None
        hh = highs[-self.lookback:]
        cc = closes[-self.lookback:]
        peaks, _ = self._find_local_extremes(hh, window=3)
        if len(peaks) < 2:
            return None
        p1, p2 = peaks[-2], peaks[-1]
        if abs(p2 - p1) < 10:
            return None
        peak1 = float(hh[p1])
        peak2 = float(hh[p2])
        if max(peak1, peak2) <= 0:
            return None
        if abs(peak1 - peak2) / max(peak1, peak2) > 0.015:
            return None
        neckline = float(min(cc[min(p1, p2) : max(p1, p2)] or [cc[0]]))
        depth_pct = (peak1 - neckline) / max(1e-9, peak1)
        conf = float(clamp(depth_pct * 10.0, 0.0, 0.8))
        return {"pattern": "DOUBLE_TOP", "confidence": conf, "neckline": neckline, "depth_pct": depth_pct * 100.0}
    def detect_double_bottom(self, lows: List[float], closes: List[float]) -> Optional[Dict[str, Any]]:
        if len(lows) < self.lookback:
            return None
        ll = lows[-self.lookback:]
        cc = closes[-self.lookback:]
        _, troughs = self._find_local_extremes(ll, window=3)
        if len(troughs) < 2:
            return None
        t1, t2 = troughs[-2], troughs[-1]
        if abs(t2 - t1) < 10:
            return None
        tr1 = float(ll[t1])
        tr2 = float(ll[t2])
        if max(tr1, tr2) <= 0:
            return None
        if abs(tr1 - tr2) / max(tr1, tr2) > 0.015:
            return None
        neckline = float(max(cc[min(t1, t2) : max(t1, t2)] or [cc[0]]))
        depth_pct = (neckline - tr1) / max(1e-9, neckline)
        conf = float(clamp(depth_pct * 10.0, 0.0, 0.8))
        return {"pattern": "DOUBLE_BOTTOM", "confidence": conf, "neckline": neckline, "depth_pct": depth_pct * 100.0}
    def detect_triangle(self, highs: List[float], lows: List[float]) -> Optional[Dict[str, Any]]:
        try:
            if len(highs) < 30 or len(lows) < 30:
                return None
            recent_highs = highs[-30:]
            recent_lows = lows[-30:]
            ht = float(np.polyfit(range(30), recent_highs, 1)[0])
            lt = float(np.polyfit(range(30), recent_lows, 1)[0])
            hs = -1 if ht < 0 else (1 if ht > 0 else 0)
            ls = -1 if lt < 0 else (1 if lt > 0 else 0)
            match (hs, ls):
                case (-1, 1):
                    ptype = "SYMMETRICAL_TRIANGLE"
                    direction = "NEUTRAL"
                case (-1, -1):
                    ptype = "DESCENDING_TRIANGLE"
                    direction = "BEARISH"
                case (1, 1):
                    ptype = "ASCENDING_TRIANGLE"
                    direction = "BULLISH"
                case _:
                    return None
            compression = abs(ht - lt) / (float(np.mean(recent_highs)) + 1e-9)
            conf = float(clamp(compression * 100.0, 0.0, 0.7))
            return {"pattern": ptype, "direction": direction, "confidence": conf, "compression": compression}
        except Exception:
            return None
    def analyze(self, history: PriceHistory) -> List[Dict[str, Any]]:
        patterns: List[Dict[str, Any]] = []
        if len(history.highs) < self.lookback or len(history.lows) < self.lookback or len(history.closes) < self.lookback:
            return patterns
        highs = list(history.highs)
        lows = list(history.lows)
        closes = list(history.closes)
        thr = float(getattr(self.cfg, "pattern_min_confidence", 0.6))
        checks = (
            (self.detect_double_top, (highs, closes)),
            (self.detect_double_bottom, (lows, closes)),
            (self.detect_triangle, (highs, lows)),
        )
        for fn, args in checks:
            res = fn(*args)
            if res and float(res.get("confidence", 0.0)) >= thr:
                patterns.append(res)
        return patterns