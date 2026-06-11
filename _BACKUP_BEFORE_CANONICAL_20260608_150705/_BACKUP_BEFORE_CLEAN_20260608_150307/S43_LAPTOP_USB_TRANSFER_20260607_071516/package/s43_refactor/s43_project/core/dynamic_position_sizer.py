from .__noop_lock import _NoopLock
from .volatility_metrics import VolatilityMetrics
from .volatility_regime import VolatilityRegime
from .position import Position

class DynamicPositionSizer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_position_size = config.get("base_position_size", 0.1)
        self.max_position_size = config.get("max_position_size", 0.25)
        self.min_position_size = config.get("min_position_size", 0.01)
        self.volatility_scaling = config.get("volatility_scaling", True)
        self.volatility_lookback = config.get("volatility_lookback_days", 20)
        self.max_daily_loss = config.get("max_daily_loss", 0.02)
        self.target_risk_reward = config.get("target_risk_reward", 2.0)
        self.kelly_fraction = config.get("kelly_fraction", 0.5)
        self.position_history: Deque[Dict[str, Any]] = __import__("collections").deque(maxlen=1000)
        self.volatility_cache: Dict[str, VolatilityMetrics] = {}
        self._lock = _NoopLock()
    def calculate_position_size(
        self,
        symbol: str,
        capital: float,
        volatility_metrics: VolatilityMetrics,
        signal_strength: float,
        current_exposure: float,
        market_regime: str
    ) -> Dict[str, Any]:
        with self._lock:
            base_size = self.base_position_size * capital
            if self.volatility_scaling:
                vol_scale = self._calculate_volatility_scale(volatility_metrics)
                base_size *= vol_scale
            signal_scale = 0.5 + abs(signal_strength)
            base_size *= min(1.5, max(0.5, signal_scale))
            regime_scale = self._get_regime_scale(market_regime)
            base_size *= regime_scale
            exposure_penalty = self._calculate_exposure_penalty(current_exposure, capital)
            base_size *= exposure_penalty
            kelly_size = self._calculate_kelly_size(
                capital, volatility_metrics, signal_strength
            )
            if kelly_size > 0:
                final_size = min(base_size, kelly_size)
            else:
                final_size = base_size
            final_size = max(
                self.min_position_size * capital,
                min(final_size, self.max_position_size * capital)
            )
            daily_loss_limit = capital * self.max_daily_loss
            max_position_for_loss = daily_loss_limit / (
                volatility_metrics.atr_percent * self.target_risk_reward
            )
            if max_position_for_loss > 0:
                final_size = min(final_size, max_position_for_loss)
            final_size = self._round_position_size(final_size, symbol)
            return {
                "position_size": final_size,
                "position_pct": final_size / capital if capital > 0 else 0,
                "base_size": base_size,
                "kelly_size": kelly_size,
                "volatility_scale": vol_scale if self.volatility_scaling else 1.0,
                "signal_scale": signal_scale,
                "regime_scale": regime_scale,
                "exposure_penalty": exposure_penalty,
                "max_daily_loss_limit": daily_loss_limit,
                "calculation_time": time.time(),
                "risk_reward_ratio": self.target_risk_reward
            }
    def _calculate_volatility_scale(self, metrics: VolatilityMetrics) -> float:
        if metrics.regime == VolatilityRegime.VERY_LOW:
            return 1.3
        elif metrics.regime == VolatilityRegime.LOW:
            return 1.1
        elif metrics.regime == VolatilityRegime.NORMAL:
            return 1.0
        elif metrics.regime == VolatilityRegime.HIGH:
            return 0.7
        elif metrics.regime == VolatilityRegime.VERY_HIGH:
            return 0.4
        else:
            return 0.1
    def _get_regime_scale(self, market_regime: str) -> float:
        regime_scales = {
            "TRENDING_UP": 1.2,
            "TRENDING_DOWN": 0.8,
            "RANGING": 0.9,
            "BREAKOUT": 1.1,
            "REVERSAL": 0.7,
            "CHOPPY": 0.6,
            "CRASH": 0.1,
            "RALLY": 1.3
        }
        return regime_scales.get(market_regime, 1.0)
    def _calculate_exposure_penalty(self, current_exposure: float, capital: float) -> float:
        if capital == 0:
            return 1.0
        exposure_ratio = current_exposure / capital
        if exposure_ratio < 0.1:
            return 1.0
        elif exposure_ratio < 0.3:
            return 0.9
        elif exposure_ratio < 0.5:
            return 0.7
        elif exposure_ratio < 0.7:
            return 0.5
        else:
            return 0.3
    def _calculate_kelly_size(
        self,
        capital: float,
        metrics: VolatilityMetrics,
        signal_strength: float
    ) -> float:
        win_prob = 0.5 + 0.25 * min(1.0, abs(signal_strength))
        if metrics.is_trending:
            win_loss_ratio = 2.0
        elif metrics.is_mean_reverting:
            win_loss_ratio = 1.5
        else:
            win_loss_ratio = 1.2
        p = win_prob
        q = 1 - win_prob
        b = win_loss_ratio
        kelly_fraction = (p * b - q) / b
        kelly_fraction *= self.kelly_fraction
        kelly_fraction = max(0.01, min(0.25, kelly_fraction))
        return kelly_fraction * capital
    def _round_position_size(self, size: float, symbol: str) -> float:
        precision_rules = {
            "BTC": 0.0001,
            "ETH": 0.001,
            "USDT": 1.0,
            "IRT": 1000.0,
        }
        for asset, precision in precision_rules.items():
            if asset in symbol:
                rounded = round(size / precision) * precision
                return max(precision, rounded)
        return round(size, 2)
    def update_volatility_metrics(
        self,
        symbol: str,
        prices: List[float],
        high_prices: Optional[List[float]] = None,
        low_prices: Optional[List[float]] = None
    ) -> VolatilityMetrics:
        if len(prices) < 20:
            return VolatilityMetrics()
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
        if not returns:
            return VolatilityMetrics()
        std_daily = statistics.stdev(returns) if len(returns) > 1 else 0
        volatility_annual = std_daily * math.sqrt(252)
        atr = 0.0
        if high_prices and low_prices and len(high_prices) == len(low_prices) == len(prices):
            true_ranges = []
            for i in range(1, len(prices)):
                high_low = high_prices[i] - low_prices[i]
                high_close = abs(high_prices[i] - prices[i-1])
                low_close = abs(low_prices[i] - prices[i-1])
                true_range = max(high_low, high_close, low_close)
                true_ranges.append(true_range)
            if true_ranges:
                atr = statistics.mean(true_ranges[-14:])
        avg_volatility = self._get_average_volatility(symbol)
        vol_ratio = volatility_annual / avg_volatility if avg_volatility > 0 else 1.0
        if vol_ratio < 0.5:
            regime = VolatilityRegime.VERY_LOW
        elif vol_ratio < 0.8:
            regime = VolatilityRegime.LOW
        elif vol_ratio < 1.2:
            regime = VolatilityRegime.NORMAL
        elif vol_ratio < 2.0:
            regime = VolatilityRegime.HIGH
        elif vol_ratio < 3.0:
            regime = VolatilityRegime.VERY_HIGH
        else:
            regime = VolatilityRegime.EXTREME
        trend_strength, trend_consistency = self._calculate_trend_metrics(prices)
        is_mean_reverting = self._is_mean_reverting(returns)
        is_trending = trend_strength > 0.3 and trend_consistency > 0.6
        is_choppy = not is_trending and not is_mean_reverting
        metrics = VolatilityMetrics(
            current_volatility=volatility_annual,
            average_volatility=avg_volatility,
            volatility_ratio=vol_ratio,
            regime=regime,
            atr=atr,
            atr_percent=(atr / prices[-1]) if prices[-1] > 0 else 0,
            std_dev=std_daily,
            var_95=self._calculate_var(returns, 0.95),
            cvar_95=self._calculate_cvar(returns, 0.95),
            trend_strength=trend_strength,
            trend_consistency=trend_consistency,
            is_mean_reverting=is_mean_reverting,
            is_trending=is_trending,
            is_choppy=is_choppy,
            calculation_time=time.time(),
            valid_until=time.time() + 300
        )
        self.volatility_cache[symbol] = metrics
        return metrics
    def _get_average_volatility(self, symbol: str) -> float:
        default_volatilities = {
            "BTC": 0.70,
            "ETH": 0.85,
            "USDT": 0.05,
            "IRT": 0.10,
        }
        for asset, vol in default_volatilities.items():
            if asset in symbol:
                return vol
        return 0.50
    def _calculate_trend_metrics(self, prices: List[float]) -> Tuple[float, float]:
        if len(prices) < 20:
            return 0.0, 0.0
        x = list(range(len(prices)))
        y = prices
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
        price_range = max(y) - min(y)
        if price_range > 0:
            normalized_slope = slope * len(prices) / price_range
            trend_strength = max(-1, min(1, normalized_slope))
        else:
            trend_strength = 0
        if len(y) > 1:
            y_mean = statistics.mean(y)
            ss_total = sum((yi - y_mean) ** 2 for yi in y)
            ss_residual = sum((yi - (slope * xi + (sum_y/n - slope * sum_x/n))) ** 2
                            for xi, yi in zip(x, y))
            if ss_total > 0:
                r_squared = 1 - (ss_residual / ss_total)
                trend_consistency = max(0, min(1, r_squared))
            else:
                trend_consistency = 0
        else:
            trend_consistency = 0
        return trend_strength, trend_consistency
    def _is_mean_reverting(self, returns: List[float]) -> bool:
        if len(returns) < 30:
            return False
        mean = statistics.mean(returns)
        variance = statistics.variance(returns) if len(returns) > 1 else 0
        if variance == 0:
            return False
        autocov = sum(
            (returns[i] - mean) * (returns[i-1] - mean)
            for i in range(1, len(returns))
        ) / (len(returns) - 1)
        autocorr = autocov / variance
        return autocorr < -0.3
    def _calculate_var(self, returns: List[float], confidence: float) -> float:
        if not returns:
            return 0.0
        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        return sorted_returns[max(0, index)] if index < len(sorted_returns) else sorted_returns[-1]
    def _calculate_cvar(self, returns: List[float], confidence: float) -> float:
        if not returns:
            return 0.0
        var = self._calculate_var(returns, confidence)
        tail_returns = [r for r in returns if r <= var]
        if tail_returns:
            return statistics.mean(tail_returns)
        return var