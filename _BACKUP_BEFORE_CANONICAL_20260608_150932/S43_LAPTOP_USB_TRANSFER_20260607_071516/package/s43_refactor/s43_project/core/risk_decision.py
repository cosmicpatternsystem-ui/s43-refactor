class RiskDecision:
    level: int
    composite: float
    size_mult: float
    allow_entries: bool
    allow_exits: bool
    reasons: Dict[str, float]
    cooldown_until: float = 0.0