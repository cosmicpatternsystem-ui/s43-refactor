from .order_book_top import OrderBookTop
from .__analytics_parsing import _AnalyticsParsing
from .logger import Logger
from .price_history import PriceHistory
from .bot_config import BotConfig

class SentimentAnalyzer:
    def __init__(self, cfg: BotConfig, logger: logging.Logger):
        self.cfg = cfg
        self._log = logger
        self.weights = _AnalyticsParsing.parse_weight_map(getattr(cfg, "sentiment_weights", "") or "", key_upper=True)
        if not self.weights:
            self.weights = {"RSI": 0.25, "VOLUME": 0.2, "DIVERGENCE": 0.3, "VOLATILITY": 0.25}
    @staticmethod
    def _atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        if len(highs) < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
            return 0.0
        trs: List[float] = []
        for i in range(1, len(highs)):
            hl = float(highs[i]) - float(lows[i])
            hc = abs(float(highs[i]) - float(closes[i - 1]))
            lc = abs(float(lows[i]) - float(closes[i - 1]))
            trs.append(max(hl, hc, lc))
        if not trs:
            return 0.0
        return float(np.mean(trs[-period:])) if len(trs) >= period else float(np.mean(trs))
    def analyze(self, history: PriceHistory, _book: Optional[OrderBookTop]) -> Dict[str, Any]:
        if not history or len(history.closes) < 20:
            return {"score": 0.0, "interpretation": "INSUFFICIENT_DATA", "indicators": {}}
        closes = list(history.closes)
        highs = list(history.highs) or closes
        lows = list(history.lows) or closes
        vols = list(history.volumes)
        rsi = _calc_rsi(closes, 14)
        rsi_score = 0.0
        if rsi > 70:
            rsi_score = -((rsi - 70.0) / 30.0)
        elif rsi < 30:
            rsi_score = (30.0 - rsi) / 30.0
        score = rsi_score * float(self.weights.get("RSI", 0.25))
        indicators: Dict[str, Any] = {"RSI": {"value": rsi, "score": rsi_score}}
        if vols and len(vols) >= 20:
            avg_v = float(np.mean(vols[-20:]))
            cur_v = float(vols[-1])
            ratio = cur_v / (avg_v + 1e-9)
            v_score = 0.0
            if ratio > float(getattr(self.cfg, "sentiment_volume_spike_threshold", 1.8) or 1.8):
                if len(closes) >= 2 and closes[-1] > closes[-2]:
                    v_score = 0.5
                elif len(closes) >= 2 and closes[-1] < closes[-2]:
                    v_score = -0.5
            indicators["VOLUME"] = {"ratio": ratio, "score": v_score}
            score += v_score * float(self.weights.get("VOLUME", 0.2))
        atr = self._atr(highs, lows, closes, 14)
        avg_px = float(np.mean(closes[-10:])) if len(closes) >= 10 else float(closes[-1])
        atr_pct = (atr / (avg_px + 1e-9)) * 100.0
        vol_score = -0.3 if atr_pct > 2.0 else (0.1 if atr_pct < 0.5 else 0.0)
        indicators["VOLATILITY"] = {"atr_pct": atr_pct, "score": vol_score}
        score += vol_score * float(self.weights.get("VOLATILITY", 0.25))
        score = float(clamp(score, -1.0, 1.0))
        interpretation = "BULLISH" if score > 0.1 else ("BEARISH" if score < -0.1 else "NEUTRAL")
        return {"score": score, "interpretation": interpretation, "indicators": indicators}