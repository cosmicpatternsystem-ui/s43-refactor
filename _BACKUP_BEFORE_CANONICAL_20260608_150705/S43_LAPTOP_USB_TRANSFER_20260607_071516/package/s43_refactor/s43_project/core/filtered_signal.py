from .priority import Priority
from .signal import Signal
from .signal_confidence import SignalConfidence
from .volatility_regime import VolatilityRegime

class FilteredSignal:
    action: str
    symbol: str
    raw_score: float
    raw_confidence: float
    filtered_score: float
    filtered_confidence: float
    confidence_level: SignalConfidence
    filters_applied: List[str]
    filter_scores: Dict[str, float]
    market_regime: str
    volatility_regime: VolatilityRegime
    trend_strength: float
    expected_win_rate: float
    expected_risk_reward: float
    position_size_pct: float
    generated_time: float
    valid_until: float
    def should_execute(self, min_confidence: float = 0.6) -> bool:
        act = str(self.action or "").upper().strip()
        return (
            act in ("BUY", "SELL") and
            self.filtered_confidence >= min_confidence and
            self.confidence_level.value >= SignalConfidence.MEDIUM.value and
            time.time() <= self.valid_until
        )
    def get_execution_priority(self) -> Priority:
        if self.confidence_level == SignalConfidence.VERY_HIGH:
            return Priority.REALTIME
        elif self.confidence_level == SignalConfidence.HIGH:
            return Priority.NORMAL
        else:
            return Priority.BACKGROUND