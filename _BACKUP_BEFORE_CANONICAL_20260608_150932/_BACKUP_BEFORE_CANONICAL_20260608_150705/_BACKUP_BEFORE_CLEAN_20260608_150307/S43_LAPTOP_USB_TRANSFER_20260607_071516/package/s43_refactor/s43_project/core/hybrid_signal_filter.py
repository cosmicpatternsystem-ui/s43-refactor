from .filtered_signal import FilteredSignal
from .signal import Signal
from .__noop_lock import _NoopLock
from .signal_confidence import SignalConfidence
from .volatility_metrics import VolatilityMetrics
from .volatility_regime import VolatilityRegime

class HybridSignalFilter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.filters = {
            "trend_filter": config.get("enable_trend_filter", True),
            "volume_filter": config.get("enable_volume_filter", True),
            "volatility_filter": config.get("enable_volatility_filter", True),
            "time_filter": config.get("enable_time_filter", True),
            "price_action_filter": config.get("enable_price_action_filter", True),
            "market_structure_filter": config.get("enable_market_structure_filter", True)
        }
        self.ema_periods = {
            "fast": config.get("ema_fast", 9),
            "medium": config.get("ema_medium", 21),
            "slow": config.get("ema_slow", 50)
        }
        self.rsi_period = config.get("rsi_period", 14)
        self.rsi_overbought = config.get("rsi_overbought", 70)
        self.rsi_oversold = config.get("rsi_oversold", 30)
        self.filter_weights = {
            "trend": config.get("trend_filter_weight", 0.25),
            "momentum": config.get("momentum_filter_weight", 0.20),
            "volume": config.get("volume_filter_weight", 0.15),
            "volatility": config.get("volatility_filter_weight", 0.15),
            "market_structure": config.get("market_structure_weight", 0.15),
            "time_based": config.get("time_filter_weight", 0.10)
        }
        self.signal_history: Dict[str, Deque[FilteredSignal]] = defaultdict(
            lambda: __import__("collections").deque(maxlen=100)
        )
        self._lock = _NoopLock()
    def filter_signal(
        self,
        raw_signal: Dict[str, Any],
        market_data: Dict[str, Any],
        volatility_metrics: VolatilityMetrics
    ) -> FilteredSignal:
        with self._lock:
            filters_applied = []
            filter_scores = {}
            total_score = 0.0
            weight_sum = 0.0
            if self.filters["trend_filter"]:
                trend_score = self._apply_trend_filter(
                    market_data, raw_signal["action"]
                )
                filter_scores["trend"] = trend_score
                total_score += trend_score * self.filter_weights["trend"]
                weight_sum += self.filter_weights["trend"]
                filters_applied.append("trend")
            if self.filters["price_action_filter"]:
                momentum_score = self._apply_momentum_filter(market_data, raw_signal["action"])
                filter_scores["momentum"] = momentum_score
                total_score += momentum_score * self.filter_weights["momentum"]
                weight_sum += self.filter_weights["momentum"]
                filters_applied.append("momentum")
            if self.filters["volume_filter"] and "volume" in market_data:
                volume_score = self._apply_volume_filter(market_data)
                filter_scores["volume"] = volume_score
                total_score += volume_score * self.filter_weights["volume"]
                weight_sum += self.filter_weights["volume"]
                filters_applied.append("volume")
            if self.filters["volatility_filter"]:
                volatility_score = self._apply_volatility_filter(
                    volatility_metrics, raw_signal["action"]
                )
                filter_scores["volatility"] = volatility_score
                total_score += volatility_score * self.filter_weights["volatility"]
                weight_sum += self.filter_weights["volatility"]
                filters_applied.append("volatility")
            if self.filters["market_structure_filter"]:
                structure_score = self._apply_market_structure_filter(market_data)
                filter_scores["market_structure"] = structure_score
                total_score += structure_score * self.filter_weights["market_structure"]
                weight_sum += self.filter_weights["market_structure"]
                filters_applied.append("market_structure")
            if self.filters["time_filter"]:
                time_score = self._apply_time_filter(raw_signal["symbol"])
                filter_scores["time_based"] = time_score
                total_score += time_score * self.filter_weights["time_based"]
                weight_sum += self.filter_weights["time_based"]
                filters_applied.append("time_based")
            if weight_sum > 0:
                final_score = total_score / weight_sum
            else:
                # All filters disabled -> keep semantics stable by normalizing raw score into [0, 1].
                raw_score = raw_signal.get("score", 0.0)
                raw_score_norm = 0.5 + 0.5 * float(clamp(float(raw_score or 0.0), -1.0, 1.0))
                final_score = raw_score_norm
            raw_score = raw_signal.get("score", 0.0)
            raw_confidence = raw_signal.get("confidence", 0.0)
            raw_score_norm = 0.5 + 0.5 * float(clamp(float(raw_score or 0.0), -1.0, 1.0))
            filtered_score = (final_score * 0.7) + (raw_score_norm * 0.3)
            filtered_confidence = (final_score * 0.6) + (raw_confidence * 0.4)
            confidence_level = self._score_to_confidence(filtered_confidence)
            market_regime = self._determine_market_regime(market_data, volatility_metrics)
            expected_win_rate, expected_risk_reward = self._calculate_expected_metrics(
                raw_signal["symbol"], filtered_score, market_regime
            )
            filtered_signal = FilteredSignal(
                action=raw_signal["action"],
                symbol=raw_signal["symbol"],
                raw_score=raw_score,
                raw_confidence=raw_confidence,
                filtered_score=filtered_score,
                filtered_confidence=filtered_confidence,
                confidence_level=confidence_level,
                filters_applied=filters_applied,
                filter_scores=filter_scores,
                market_regime=market_regime,
                volatility_regime=volatility_metrics.regime,
                trend_strength=volatility_metrics.trend_strength,
                expected_win_rate=expected_win_rate,
                expected_risk_reward=expected_risk_reward,
                position_size_pct=0.0,
                generated_time=time.time(),
                valid_until=time.time() + 60
            )
            self.signal_history[raw_signal["symbol"]].append(filtered_signal)
            return filtered_signal
    def _apply_trend_filter(self, market_data: Dict[str, Any], action: str) -> float:
        ema_fast = market_data.get("ema_fast")
        ema_medium = market_data.get("ema_medium")
        ema_slow = market_data.get("ema_slow")
        current_price = market_data.get("price")
        if None in (ema_fast, ema_medium, ema_slow, current_price):
            return 0.5
        is_uptrend = (
            current_price > ema_fast > ema_medium > ema_slow
        )
        is_downtrend = (
            current_price < ema_fast < ema_medium < ema_slow
        )
        if action == "BUY":
            if is_uptrend:
                return 1.0
            elif not is_downtrend:
                return 0.7
            else:
                return 0.3
        elif action == "SELL":
            if is_downtrend:
                return 1.0
            elif not is_uptrend:
                return 0.7
            else:
                return 0.3
        else:
            return 0.5
    def _apply_momentum_filter(self, market_data: Dict[str, Any], action: str) -> float:
        rsi = market_data.get("rsi")
        if rsi is None:
            return 0.5
        act = str(action or "").upper()
        if rsi > self.rsi_overbought:
            return 0.2 if act == "BUY" else 0.9
        elif rsi < self.rsi_oversold:
            return 0.9 if act == "BUY" else 0.2
        elif 40 <= rsi <= 60:
            return 0.8
        elif (30 <= rsi < 40) or (60 < rsi <= 70):
            return 0.6
        else:
            return 0.4
    def _apply_volume_filter(self, market_data: Dict[str, Any]) -> float:
        volume = market_data.get("volume")
        avg_volume = market_data.get("avg_volume")
        if volume is None or avg_volume is None or avg_volume == 0:
            return 0.5
        volume_ratio = volume / avg_volume
        if volume_ratio > 1.5:
            return 1.0
        elif volume_ratio > 1.2:
            return 0.8
        elif volume_ratio > 0.8:
            return 0.6
        elif volume_ratio > 0.5:
            return 0.4
        else:
            return 0.2
    def _apply_volatility_filter(
        self,
        volatility_metrics: VolatilityMetrics,
        action: str
    ) -> float:
        regime = volatility_metrics.regime
        if regime == VolatilityRegime.VERY_LOW:
            return 0.8 if action in ["BUY", "SELL"] else 0.5
        elif regime == VolatilityRegime.LOW:
            return 0.9
        elif regime == VolatilityRegime.NORMAL:
            return 1.0
        elif regime == VolatilityRegime.HIGH:
            return 0.7
        elif regime == VolatilityRegime.VERY_HIGH:
            return 0.4
        else:
            return 0.1
    def _apply_market_structure_filter(self, market_data: Dict[str, Any]) -> float:
        price = market_data.get("price")
        support = market_data.get("support_level")
        resistance = market_data.get("resistance_level")
        if None in (price, support, resistance):
            return 0.5
        price_range = resistance - support
        if price_range == 0:
            return 0.5
        distance_to_support = (price - support) / price_range
        distance_to_resistance = (resistance - price) / price_range
        if distance_to_support < 0.1 or distance_to_resistance < 0.1:
            return 0.9
        elif 0.4 < distance_to_support < 0.6:
            return 0.7
        else:
            return 0.5
    def _apply_time_filter(self, symbol: str) -> float:
        recent_signals = list(self.signal_history.get(symbol, []))
        if not recent_signals:
            return 0.7
        recent_count = len([s for s in recent_signals
                          if time.time() - s.generated_time < 3600])
        if recent_count > 5:
            return 0.3
        elif recent_count > 3:
            return 0.6
        else:
            return 0.9
    def _score_to_confidence(self, score: float) -> SignalConfidence:
        if score >= 0.9:
            return SignalConfidence.VERY_HIGH
        elif score >= 0.8:
            return SignalConfidence.HIGH
        elif score >= 0.7:
            return SignalConfidence.MEDIUM
        elif score >= 0.6:
            return SignalConfidence.LOW
        else:
            return SignalConfidence.VERY_LOW
    def _determine_market_regime(
        self,
        market_data: Dict[str, Any],
        volatility_metrics: VolatilityMetrics
    ) -> str:
        trend_strength = abs(volatility_metrics.trend_strength)
        if volatility_metrics.is_trending:
            if volatility_metrics.trend_strength > 0:
                return "TRENDING_UP"
            else:
                return "TRENDING_DOWN"
        elif volatility_metrics.is_mean_reverting:
            return "RANGING"
        elif volatility_metrics.is_choppy:
            return "CHOPPY"
        elif trend_strength > 0.5:
            if "breakout" in market_data.get("patterns", []):
                return "BREAKOUT"
            else:
                return "TRENDING"
        else:
            return "NEUTRAL"
    def _calculate_expected_metrics(
        self,
        symbol: str,
        signal_score: float,
        market_regime: str
    ) -> Tuple[float, float]:
        base_win_rate = 0.55
        base_rr = 1.5
        win_rate_adjustment = (signal_score - 0.5) * 0.3
        rr_adjustment = (signal_score - 0.5) * 0.5
        regime_multipliers = {
            "TRENDING_UP": (1.1, 1.2),
            "TRENDING_DOWN": (1.05, 1.1),
            "BREAKOUT": (1.15, 1.3),
            "RANGING": (0.95, 0.9),
            "CHOPPY": (0.9, 0.8),
            "NEUTRAL": (1.0, 1.0)
        }
        regime_mult = regime_multipliers.get(market_regime, (1.0, 1.0))
        expected_win_rate = min(0.85, max(0.4,
            base_win_rate + win_rate_adjustment * regime_mult[0]
        ))
        expected_rr = min(3.0, max(1.0,
            base_rr + rr_adjustment * regime_mult[1]
        ))
        return expected_win_rate, expected_rr