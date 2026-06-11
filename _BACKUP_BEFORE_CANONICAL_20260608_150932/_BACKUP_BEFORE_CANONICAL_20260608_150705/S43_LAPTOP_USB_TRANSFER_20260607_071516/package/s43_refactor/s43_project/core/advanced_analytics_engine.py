from .order_book_top import OrderBookTop
from .order_book_analyzer import OrderBookAnalyzer
from .logger import Logger
from .price_history import PriceHistory
from .multi_timeframe_analyzer import MultiTimeframeAnalyzer
from .light_ml_predictor import LightMLPredictor
from .sentiment_analyzer import SentimentAnalyzer
from .bot_config import BotConfig
from .pattern_detector import PatternDetector
from .data_feed import DataFeed

class AdvancedAnalyticsEngine:
    def __init__(self, cfg: BotConfig, logger: logging.Logger, feed: "DataFeed"):
        self.cfg = cfg
        self._log = logger
        self.feed = feed
        self.price_history: Dict[str, Dict[str, PriceHistory]] = {}
        self.history_last_update: Dict[str, float] = {}
        self.multi_timeframe = MultiTimeframeAnalyzer(cfg, logger) if bool(getattr(cfg, "multi_timeframe_enabled", True)) else None
        self.pattern_detector = PatternDetector(cfg, logger) if bool(getattr(cfg, "pattern_detection_enabled", True)) else None
        self.order_book_analyzer = OrderBookAnalyzer(cfg, logger) if bool(getattr(cfg, "order_book_analysis_enabled", True)) else None
        self.sentiment_analyzer = SentimentAnalyzer(cfg, logger) if bool(getattr(cfg, "sentiment_analysis_enabled", True)) else None
        self.ml_predictor = LightMLPredictor(cfg, logger) if bool(getattr(cfg, "ml_predictor_enabled", True)) else None
        self._log.info(
            "AdvancedAnalyticsEngine layers=%d",
            sum(1 for x in [self.multi_timeframe, self.pattern_detector, self.order_book_analyzer, self.sentiment_analyzer, self.ml_predictor] if x is not None),
        )
    def _ensure_hist(self, symbol: str, tf: str) -> PriceHistory:
        if symbol not in self.price_history:
            self.price_history[symbol] = {}
        if tf not in self.price_history[symbol]:
            self.price_history[symbol][tf] = PriceHistory(symbol=symbol)
        return self.price_history[symbol][tf]
    def _estimate_volume(self, book: OrderBookTop) -> float:
        try:
            b = sum(float(x.get("amount") or x.get("quantity") or 0.0) for x in (book.bids or [])[:5] if isinstance(x, dict))
            a = sum(float(x.get("amount") or x.get("quantity") or 0.0) for x in (book.asks or [])[:5] if isinstance(x, dict))
            v = b + a
            return float(v) if v > 0 else 100.0
        except Exception:
            return 100.0
    def _rebuild_timeframes(self, base: PriceHistory) -> Dict[str, PriceHistory]:
        tfs = {"5m": 5, "15m": 15, "30m": 30, "1h": 60}
        result: Dict[str, PriceHistory] = {}
        closes = list(base.closes)
        highs = list(base.highs)
        lows = list(base.lows)
        opens = list(base.opens)
        vols = list(base.volumes)
        ts = list(base.timestamps)
        n = len(closes)
        for tf, g in tfs.items():
            if n < g:
                continue
            agg = PriceHistory(symbol=base.symbol)
            for i in range(0, n, g):
                j = min(i + g, n)
                if j - i < g:
                    continue
                agg.timestamps.append(float(ts[j - 1]))
                agg.opens.append(float(opens[i]))
                agg.highs.append(float(max(highs[i:j])))
                agg.lows.append(float(min(lows[i:j])))
                agg.closes.append(float(closes[j - 1]))
                agg.volumes.append(float(sum(vols[i:j])))
            result[tf] = agg
        return result
    async def update_price_history(self, symbol: str, book: Optional[OrderBookTop]) -> bool:
        symbol = _canon_symbol(symbol)
        if not book:
            return False
        now = time.time()
        last_update = float(self.history_last_update.get(symbol, 0.0))
        if (now - last_update) < float(getattr(self.cfg, "history_refresh_interval", 2.0) or 2.0):
            return True
        base = self._ensure_hist(symbol, "1m")
        mid = float(getattr(book, "mid", 0.0) or 0.0)
        spot = None
        if mid <= 0.0:
            try:
                rec = getattr(self.feed, "_spot_cache", {}).get(symbol)
                if rec:
                    _ts, _px = rec
                    if _px is not None:
                        spot = float(_px)
            except Exception:
                spot = None
            if spot is None:
                try:
                    tmo = float(_env_float("HISTORY_SPOT_FALLBACK_TIMEOUT_SEC", 2.0) or 2.0)
                except Exception:
                    tmo = 2.0
                tmo = max(0.5, min(6.0, float(tmo)))
                try:
                    spot = await asyncio.wait_for(self.feed.fetch_spot(symbol), timeout=tmo)
                except Exception:
                    spot = None
        if mid <= 0.0 and spot is not None:
            try:
                mid = float(spot or 0.0)
            except Exception:
                pass
        if mid <= 0.0:
            return False
        vol = self._estimate_volume(book)
        base.timestamps.append(now)
        base.opens.append(mid)
        base.highs.append(mid * 1.0005)
        base.lows.append(mid * 0.9995)
        base.closes.append(mid)
        base.volumes.append(vol)
        base.last_update = now
        maxlen = int(getattr(self.cfg, "price_history_bars", 200) or 200)
        for dq in [base.timestamps, base.opens, base.highs, base.lows, base.closes, base.volumes]:
            try:
                for _omega_guard in range(150000):
                    dq.popleft()
            except Exception:
                pass
        derived = self._rebuild_timeframes(base)
        for tf, hist in derived.items():
            self.price_history[symbol][tf] = hist
        self.history_last_update[symbol] = now
        return True

    async def analyze_symbol(self, symbol: str, book: Optional[OrderBookTop]) -> Dict[str, Any]:
        symbol = _canon_symbol(symbol)
        analysis: Dict[str, Any] = {"symbol": symbol, "timestamp": time.time(), "layers": {}, "composite_score": 0.0, "recommendation": "HOLD"}
        await self.update_price_history(symbol, book)
        history_by_tf = self.price_history.get(symbol) or {}
        base = history_by_tf.get("1m")
        if not base:
            analysis["error"] = "INSUFFICIENT_HISTORY"
            return analysis
        layers = analysis["layers"]
        if self.multi_timeframe:
            try:
                layers["multi_timeframe"] = self.multi_timeframe.analyze(symbol, history_by_tf)
            except Exception as e:
                self._log.error("AA MTF failed %s: %s", symbol, e)
        if self.pattern_detector:
            try:
                layers["patterns"] = self.pattern_detector.analyze(base)
            except Exception as e:
                self._log.error("AA patterns failed %s: %s", symbol, e)
        if self.order_book_analyzer and book:
            try:
                layers["order_book"] = self.order_book_analyzer.analyze(book)
            except Exception as e:
                self._log.error("AA order book failed %s: %s", symbol, e)
        if self.sentiment_analyzer:
            try:
                layers["sentiment"] = self.sentiment_analyzer.analyze(base, book)
            except Exception as e:
                self._log.error("AA sentiment failed %s: %s", symbol, e)
        if self.ml_predictor:
            try:
                feats = self.ml_predictor._extract_features(base, book)
                layers["ml_prediction"] = self.ml_predictor.predict(feats)
            except Exception as e:
                self._log.error("AA ml failed %s: %s", symbol, e)
        composite = self._compute_composite_score(layers)
        analysis["composite_score"] = float(composite)
        analysis["recommendation"] = self._generate_recommendation(float(composite), layers)
        analysis["signal_boost"] = self._calculate_signal_boost(float(composite))
        analysis["confidence_boost"] = self._calculate_confidence_boost(layers)
        return analysis
    def _compute_composite_score(self, layers: Dict[str, Any]) -> float:
        scores: List[float] = []
        weights: List[float] = []
        mtf = layers.get("multi_timeframe")
        if isinstance(mtf, dict) and bool(mtf.get("passed")):
            scores.append(float(mtf.get("score", 0.0)))
            weights.append(0.30)
        ob = layers.get("order_book")
        if isinstance(ob, dict):
            scores.append(float(ob.get("score", 0.0)))
            weights.append(0.25)
        sent = layers.get("sentiment")
        if isinstance(sent, dict):
            scores.append(float(sent.get("score", 0.0)))
            weights.append(0.25)
        ml = layers.get("ml_prediction")
        if isinstance(ml, dict):
            scores.append(float(ml.get("score", 0.0)))
            weights.append(0.20)
        pats = layers.get("patterns")
        if isinstance(pats, list) and pats:
            pattern_bias = {
                "DOUBLE_BOTTOM": 0.5,
                "ASCENDING_TRIANGLE": 0.5,
                "DOUBLE_TOP": -0.5,
                "DESCENDING_TRIANGLE": -0.5,
            }
            for p in pats:
                try:
                    if float(p.get("confidence", 0.0)) > 0.7:
                        bias = pattern_bias.get(str(p.get("pattern", "") or ""))
                        if bias is not None:
                            scores.append(float(bias))
                            weights.append(0.10)
                except Exception:
                    continue
        if not scores or not weights:
            return 0.0
        tw = sum(weights)
        if tw <= 0:
            return 0.0
        return float(sum(s * w for s, w in zip(scores, weights)) / tw)
    @staticmethod
    def _generate_recommendation(composite: float, layers: Dict[str, Any]) -> str:
        for thr, rec in ((0.40, "STRONG_BUY"), (0.20, "BUY")):
            if composite > thr:
                return rec
        for thr, rec in ((-0.40, "STRONG_SELL"), (-0.20, "SELL")):
            if composite < thr:
                return rec
        pats = layers.get("patterns")
        if isinstance(pats, list):
            overrides = {"DOUBLE_BOTTOM": "BUY", "DOUBLE_TOP": "SELL"}
            for p in pats:
                try:
                    if float(p.get("confidence", 0.0)) > 0.7:
                        o = overrides.get(str(p.get("pattern", "") or ""))
                        if o:
                            return o
                except Exception:
                    continue
        return "HOLD"
    def _calculate_signal_boost(self, composite: float) -> float:
        base = float(getattr(self.cfg, "analytics_signal_boost", 1.25) or 1.25)
        a = abs(float(composite))
        if a > 0.5:
            return float(clamp(base * 1.2, 1.0, 2.0))
        if a > 0.3:
            return float(clamp(base, 1.0, 2.0))
        if a > 0.1:
            return float(clamp(1.0 + (base - 1.0) * 0.5, 1.0, 2.0))
        return 1.0
    def _calculate_confidence_boost(self, layers: Dict[str, Any]) -> float:
        base = float(getattr(self.cfg, "analytics_confidence_boost", 1.15) or 1.15)
        active = 0
        score_list: List[float] = []
        for k in ("multi_timeframe", "order_book", "sentiment", "ml_prediction"):
            v = layers.get(k)
            if isinstance(v, dict):
                active += 1
                score_list.append(float(v.get("score", 0.0)))
        pats = layers.get("patterns")
        if isinstance(pats, list) and pats:
            active += 1
        max_layers = 5
        layer_conf = active / max_layers
        consistency = 1.0
        try:
            if len(score_list) >= 2 and any(abs(s) > 1e-9 for s in score_list):
                std = float(np.std(score_list))
                max_abs = max(abs(s) for s in score_list) + 1e-9
                consistency = float(clamp(1.0 - (std / max_abs), 0.0, 1.0))
        except Exception:
            pass
        boost = 1.0 + (base - 1.0) * layer_conf * consistency
        return float(clamp(boost, 1.0, 2.0))