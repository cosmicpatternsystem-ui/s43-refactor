from .order_book_top import OrderBookTop
from .logger import Logger
from .price_history import PriceHistory
from .bot_config import BotConfig

class LightMLPredictor:
    def __init__(self, cfg: BotConfig, logger: logging.Logger):
        self.cfg = cfg
        self._log = logger
        self._model = {
            "weights": {
                "price_momentum": 0.35,
                "volume_trend": 0.25,
                "spread_ratio": 0.15,
                "time_of_day": 0.10,
                "volatility": 0.15,
            },
            "bias": 0.0,
        }
    def _extract_features(self, history: PriceHistory, book: Optional[OrderBookTop]) -> Dict[str, float]:
        feats: Dict[str, float] = {}
        if not history or len(history.closes) < 10:
            return feats
        closes = list(history.closes)
        vols = list(history.volumes)
        if len(closes) >= 10:
            short_ma = float(np.mean(closes[-5:]))
            med_ma = float(np.mean(closes[-10:]))
            feats["price_momentum"] = (short_ma / (med_ma + 1e-9) - 1.0) * 100.0
        if vols and len(vols) >= 10:
            recent_v = float(np.mean(vols[-3:]))
            past_v = float(np.mean(vols[-10:-3]))
            feats["volume_trend"] = (recent_v / (past_v + 1e-9) - 1.0) * 100.0
        if book and float(getattr(book, "bid", 0.0)) > 0 and float(getattr(book, "ask", 0.0)) > 0:
            bid = float(book.bid)
            ask = float(book.ask)
            spread_bps = (ask - bid) / ((ask + bid) / 2.0) * 10000.0
            feats["spread_ratio"] = spread_bps / 100.0
        hour = datetime.datetime.now().hour
        feats["time_of_day"] = 1.0 if 9 <= hour <= 12 else (0.5 if 13 <= hour <= 16 else 0.0)
        if len(closes) >= 10:
            rets = [(float(closes[i]) / float(closes[i - 1]) - 1.0) * 100.0 for i in range(1, len(closes))]
            feats["volatility"] = float(np.std(rets[-10:])) if rets else 0.0
        return feats
    def predict(self, feats: Dict[str, float]) -> Dict[str, Any]:
        if not feats:
            return {"direction": "NEUTRAL", "score": 0.0, "confidence": 0.0}
        w = self._model["weights"]
        score = float(self._model["bias"]) + float(sum(float(feats[k]) * float(w[k]) for k in w if k in feats))
        score = float(clamp(score / 100.0, -1.0, 1.0))
        used = sum(1 for k in w if k in feats)
        conf = float(used / max(1, len(w)))
        direction = "UP" if score > 0.1 else ("DOWN" if score < -0.1 else "NEUTRAL")
        return {"direction": direction, "score": score, "confidence": conf, "features_used": list(feats.keys())}