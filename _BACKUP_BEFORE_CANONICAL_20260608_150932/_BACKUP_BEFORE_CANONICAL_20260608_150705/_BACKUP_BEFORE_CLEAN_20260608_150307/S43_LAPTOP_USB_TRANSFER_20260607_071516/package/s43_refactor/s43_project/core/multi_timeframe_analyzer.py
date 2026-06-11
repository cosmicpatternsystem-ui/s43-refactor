from .__analytics_parsing import _AnalyticsParsing
from .logger import Logger
from .price_history import PriceHistory
from .bot_config import BotConfig

class MultiTimeframeAnalyzer:
    def __init__(self, cfg: BotConfig, logger: logging.Logger):
        self.cfg = cfg
        self._log = logger
        self.weights = _AnalyticsParsing.parse_weight_map(getattr(cfg, "mtf_weights", "") or "")
        if not self.weights:
            self.weights = {"1m": 0.2, "5m": 0.3, "15m": 0.25, "30m": 0.15, "1h": 0.1}
    @staticmethod
    def _ema(prices: List[float], period: int) -> float:
        if not prices:
            return 0.0
        if len(prices) < period:
            return float(prices[-1])
        alpha = 2.0 / (period + 1.0)
        ema = float(prices[0])
        for p in prices[1:]:
            ema = alpha * float(p) + (1.0 - alpha) * ema
        return float(ema)
    @staticmethod
    def _score_trend(ma_fast: float, ma_slow: float, rsi: float) -> float:
        if ma_slow <= 0:
            return 0.0
        ma_score = (ma_fast - ma_slow) / ma_slow * 10.0
        rsi_score = 0.0
        if rsi > 70:
            rsi_score = -((rsi - 70.0) / 30.0)
        elif rsi < 30:
            rsi_score = (30.0 - rsi) / 30.0
        return float(clamp(ma_score * 0.7 + rsi_score * 0.3, -1.0, 1.0))
    def analyze(self, _symbol: str, history_by_tf: Dict[str, PriceHistory]) -> Dict[str, Any]:
        scores: List[float] = []
        used: List[str] = []
        for tf, w in self.weights.items():
            hist = history_by_tf.get(tf)
            if not hist or len(hist.closes) < 50:
                continue
            closes = list(hist.closes)
            ma_fast = self._ema(closes[-12:], 12)
            ma_slow = self._ema(closes[-50:], 50)
            rsi = _calc_rsi(closes, 14)
            s = self._score_trend(ma_fast, ma_slow, rsi)
            scores.append(float(s) * float(w))
            used.append(tf)
        if not scores or not used:
            return {"trend": "UNKNOWN", "strength": 0.0, "score": 0.0, "confidence": 0.0, "available_tfs": [], "passed": False}
        denom = sum(self.weights.get(tf, 0.0) for tf in used) or 1.0
        avg_score = float(sum(scores) / denom)
        trend = "BULLISH" if avg_score > 0.3 else ("BEARISH" if avg_score < -0.3 else "SIDEWAYS")
        confidence = float(len(used) / max(1, len(self.weights)))
        passed = bool(confidence >= float(getattr(self.cfg, "mtf_min_confidence", 0.65)))
        return {"trend": trend, "strength": abs(avg_score), "score": avg_score, "confidence": confidence, "available_tfs": used, "passed": passed}