from .volatility_regime import VolatilityRegime

class VolatilityMetrics:
    current_volatility: float = 0.0
    average_volatility: float = 0.0
    volatility_ratio: float = 1.0
    regime: VolatilityRegime = VolatilityRegime.NORMAL
    atr: float = 0.0
    atr_percent: float = 0.0
    std_dev: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0
    trend_strength: float = 0.0
    trend_consistency: float = 0.0
    is_mean_reverting: bool = False
    is_trending: bool = False
    is_choppy: bool = False
    calculation_time: float = 0.0
    valid_until: float = 0.0