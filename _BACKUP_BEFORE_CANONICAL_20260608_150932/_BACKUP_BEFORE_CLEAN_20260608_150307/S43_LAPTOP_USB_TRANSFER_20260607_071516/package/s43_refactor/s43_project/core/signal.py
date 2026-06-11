class Signal:
    action: str
    symbol: str
    score: float
    confidence: float
    price: float
    reason: str
    meta: Dict[str, Any] = field(default_factory=dict)
    market: str = "spot"
    strategy_family: str = "spot"
    regime: str = "neutral"
    leverage: float = 1.0
    reduce_only: bool = False
    risk_level: str = "normal"
    ai_assisted: bool = False
    ai_advice: Optional[str] = None